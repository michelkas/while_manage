from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Min, Sum
from django.utils import timezone

from .models import Article, In, Out, OutAllocation, StockEntry, WeeklyReport


def allocate_expense(expense):
    """Répartit une sortie sur les recettes disponibles, du plus ancien au plus récent (FIFO)."""
    with transaction.atomic():
        incomes = (
            In.objects.select_for_update()
            .filter(date__lte=expense.date)
            .values('date__year', 'date__month')
            .annotate(total=Sum('total_price'))
            .order_by('date__year', 'date__month')
        )
        used = defaultdict(lambda: Decimal('0.00'))
        for allocation in OutAllocation.objects.select_for_update().values('year', 'month').annotate(total=Sum('amount')):
            used[(allocation['year'], allocation['month'])] = allocation['total']

        remaining = expense.amount
        allocations = []
        for item in incomes:
            year, month_number = item['date__year'], item['date__month']
            month = f'{month_number:02d}'
            available = item['total'] - used[(year, month)]
            if available <= 0:
                continue
            taken = min(available, remaining)
            allocations.append(OutAllocation(out=expense, year=year, month=month, amount=taken))
            remaining -= taken
            if remaining == 0:
                break

        if remaining > 0:
            raise ValidationError("Solde insuffisant : cette dépense dépasse les entrées disponibles jusqu'à sa date.")
        OutAllocation.objects.bulk_create(allocations)


def delete_article(article):
    """Supprime un article et son historique sans utiliser le collecteur Django."""
    using = article._state.db or 'default'
    with transaction.atomic(using=using):
        In.objects.using(using).filter(article_id=article.pk)._raw_delete(using=using)
        StockEntry.objects.using(using).filter(article_id=article.pk)._raw_delete(using=using)
        Article.objects.using(using).filter(pk=article.pk)._raw_delete(using=using)


def close_completed_weeks(today=None):
    """Sauvegarde les semaines closes ayant une activité, sans créer de semaine vide ou future."""
    today = today or timezone.localdate()
    last_completed_sunday = today - timedelta(days=today.weekday() + 1)
    first_sale = In.objects.aggregate(first=Min('date'))['first']
    first_expense = Out.objects.aggregate(first=Min('date'))['first']
    first_operation = min((item for item in (first_sale, first_expense) if item), default=None)
    if not first_operation or first_operation > last_completed_sunday:
        return

    week_start = first_operation - timedelta(days=first_operation.weekday())
    while week_start <= last_completed_sunday:
        week_end = week_start + timedelta(days=6)
        income = In.objects.filter(date__range=(week_start, week_end)).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        expense = Out.objects.filter(date__range=(week_start, week_end)).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        if income or expense:
            WeeklyReport.objects.update_or_create(
                week_start=week_start,
                defaults={
                    'week_end': week_end, 'income_total': income,
                    'expense_total': expense, 'balance_total': income - expense,
                },
            )
        week_start += timedelta(weeks=1)
