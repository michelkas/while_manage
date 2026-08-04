from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import In, Out, OutAllocation


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
