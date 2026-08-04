from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import ArticleForm, ExpenseForm, IncomeForm, StockEntryForm
from .models import Article, In, Out, OutAllocation, StockEntry
from .services import allocate_expense


@login_required
def dashboard(request):
    today = timezone.localdate()
    try:
        selected_month = int(request.GET.get('month', today.month))
        selected_year = int(request.GET.get('year', today.year))
        if not 1 <= selected_month <= 12:
            raise ValueError
    except ValueError:
        selected_month, selected_year = today.month, today.year

    sales = In.objects.filter(date__year=selected_year, date__month=selected_month).select_related('article')
    expenses = Out.objects.filter(date__year=selected_year, date__month=selected_month).prefetch_related('allocations')
    income_total = sales.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    expense_total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    selected_code = f'{selected_month:02d}'
    selected_name = dict(Out._meta.get_field('month').choices)[selected_code]
    allocated = OutAllocation.objects.filter(year=selected_year, month=selected_code).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    articles = Article.objects.order_by('name')
    stock_value = sum((article.price * article.quantity for article in articles), Decimal('0.00'))
    total_received = In.objects.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    total_allocated = OutAllocation.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    incomes_by_month = {
        item['date__month']: item['total']
        for item in In.objects.filter(date__year=selected_year).values('date__month').annotate(total=Sum('total_price'))
    }
    expenses_by_month = {
        item['date__month']: item['total']
        for item in Out.objects.filter(date__year=selected_year).values('date__month').annotate(total=Sum('amount'))
    }
    chart_peak = max([*incomes_by_month.values(), *expenses_by_month.values(), Decimal('1.00')])
    month_labels = dict(Out._meta.get_field('month').choices)
    monthly_chart = []
    for number in range(1, 13):
        income = incomes_by_month.get(number, Decimal('0.00'))
        expense = expenses_by_month.get(number, Decimal('0.00'))
        monthly_chart.append({
            'label': month_labels[f'{number:02d}'][:3], 'income': income, 'expense': expense,
            'income_height': max(3, int(income * 100 / chart_peak)),
            'expense_height': max(3, int(expense * 100 / chart_peak)),
        })

    return render(request, 'data/dashboard.html', {
        'article_form': ArticleForm(), 'stock_entry_form': StockEntryForm(), 'income_form': IncomeForm(), 'expense_form': ExpenseForm(),
        'articles': articles, 'sales': sales, 'expenses': expenses, 'recent_entries': StockEntry.objects.select_related('article')[:5],
        'income_total': income_total, 'expense_total': expense_total,
        'available_total': income_total - allocated, 'cash_available': total_received - total_allocated,
        'stock_value': stock_value, 'low_stock': [article for article in articles if article.needs_restock],
        'monthly_chart': monthly_chart,
        'selected_month': selected_month, 'selected_year': selected_year,
        'selected_month_name': selected_name, 'months': [(number, label) for number, label in enumerate(dict(Out._meta.get_field('month').choices).values(), 1)],
    })


@login_required
def create_article(request):
    if request.method != 'POST':
        return redirect('dashboard')
    form = ArticleForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Article ajouté au stock.')
    else:
        messages.error(request, 'Article non enregistré : vérifiez les champs.')
    return redirect('dashboard')


@login_required
def create_stock_entry(request):
    if request.method != 'POST':
        return redirect('dashboard')
    form = StockEntryForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Réapprovisionnement enregistré. Le stock a été mis à jour.')
    else:
        messages.error(request, 'Réapprovisionnement non enregistré : vérifiez les champs.')
    return redirect('dashboard')


@login_required
def create_income(request):
    if request.method != 'POST':
        return redirect('dashboard')
    form = IncomeForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Vente enregistrée et stock mis à jour.')
    else:
        messages.error(request, 'Vente non enregistrée : vérifiez le stock et la date.')
    return redirect('dashboard')


@login_required
def create_expense(request):
    if request.method != 'POST':
        return redirect('dashboard')
    form = ExpenseForm(request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                expense = form.save()
                allocate_expense(expense)
            messages.success(request, 'Dépense enregistrée et répartie sur les mois disponibles.')
        except ValidationError as error:
            messages.error(request, error.messages[0])
    else:
        messages.error(request, 'Dépense non enregistrée : vérifiez les informations saisies.')
    return redirect('dashboard')
