from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Article, In, Out, OutAllocation, StockEntry, WeeklyReport
from .services import allocate_expense, close_completed_weeks


class CashManagementTests(TestCase):
    def setUp(self):
        self.article = Article.objects.create(name='Sac', description='', price=Decimal('10.00'), quantity=20)

    def sale(self, when, quantity, price):
        return In.objects.create(
            article=self.article, quantity=quantity, unit_price=Decimal(price),
            date=when, total_price=Decimal('0'),
        )

    def test_sale_calculates_total_and_decreases_stock(self):
        sale = self.sale(date(2026, 1, 5), 3, '15.50')
        self.article.refresh_from_db()
        self.assertEqual(sale.total_price, Decimal('46.50'))
        self.assertEqual(self.article.quantity, 17)
        self.assertEqual(sale.month, '01')

    def test_sale_accepts_float_unit_price_backend(self):
        sale = In.objects.create(
            article=self.article,
            quantity=3,
            unit_price=15.5,
            cost_price=Decimal('10.00'),
            date=date(2026, 1, 5),
            total_price=Decimal('0')
        )
        self.assertEqual(sale.unit_price, Decimal('15.50'))
        self.assertEqual(sale.total_price, Decimal('46.50'))

    def test_sale_accepts_float_quantity_backend(self):
        sale = In.objects.create(
            article=self.article,
            quantity=1.5,
            unit_price=Decimal('10.00'),
            cost_price=Decimal('8.00'),
            date=date(2026, 1, 5),
            total_price=Decimal('0')
        )
        self.assertEqual(sale.quantity, Decimal('1.50'))
        self.assertEqual(sale.total_price, Decimal('15.00'))

    def test_april_expense_uses_january_then_february_then_march(self):
        self.sale(date(2026, 1, 10), 1, '1500.00')
        self.sale(date(2026, 2, 10), 1, '6000.00')
        self.sale(date(2026, 3, 10), 1, '9000.00')
        expense = Out.objects.create(description='Dépense avril', amount=Decimal('15500.00'), date=date(2026, 4, 12))
        allocate_expense(expense)
        allocations = {item.month: item.amount for item in OutAllocation.objects.filter(out=expense)}
        self.assertEqual(expense.month, '04')
        self.assertEqual(allocations, {'01': Decimal('1500.00'), '02': Decimal('6000.00'), '03': Decimal('8000.00')})

    def test_restock_increases_quantity(self):
        StockEntry.objects.create(article=self.article, quantity=12, unit_cost=Decimal('12.00'), date=date(2026, 1, 2))
        self.article.refresh_from_db()
        self.assertEqual(self.article.quantity, 32)
        self.assertEqual(self.article.price, Decimal('12.00'))

    def test_only_completed_weeks_with_activity_are_saved(self):
        self.sale(date(2026, 1, 6), 2, '20.00')
        Out.objects.create(description='Transport', amount=Decimal('10.00'), date=date(2026, 1, 9))
        close_completed_weeks(today=date(2026, 1, 12))
        report = WeeklyReport.objects.get(week_start=date(2026, 1, 5))
        self.assertEqual(report.week_end, date(2026, 1, 11))
        self.assertEqual(report.income_total, Decimal('40.00'))
        self.assertEqual(report.expense_total, Decimal('10.00'))
        self.assertEqual(report.balance_total, Decimal('30.00'))
        self.assertEqual(WeeklyReport.objects.count(), 1)


class AccessControlTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='gerant', password='mot-de-passe-fort-2026')
        self.article = Article.objects.create(name='Sac', description='', price=Decimal('10.00'), quantity=20)

    def sale(self, when, quantity, price):
        return In.objects.create(
            article=self.article, quantity=quantity, unit_price=Decimal(price),
            date=when, total_price=Decimal('0'),
        )

    def test_dashboard_requires_authentication(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/connexion/?next=/')

    def test_user_can_login_and_open_dashboard(self):
        response = self.client.post('/connexion/', {'username': 'gerant', 'password': 'mot-de-passe-fort-2026'})
        self.assertRedirects(response, '/')
        self.assertContains(self.client.get('/'), 'Rapports hebdomadaires clôturés')

    def test_expense_is_split_between_months(self):
        self.sale(date(2026, 1, 5), 3, '10.00')
        self.sale(date(2026, 2, 6), 4, '10.00')
        expense = Out.objects.create(description='Loyer', amount=Decimal('55.00'), date=date(2026, 2, 20))
        allocate_expense(expense)
        allocations = OutAllocation.objects.filter(out=expense).order_by('month')
        self.assertEqual(allocations.count(), 2)
        self.assertEqual(sum(item.amount for item in allocations), Decimal('55.00'))
        self.assertEqual(OutAllocation.objects.get(out=expense, month='02').amount, Decimal('25.00'))
        self.assertEqual(OutAllocation.objects.get(out=expense, month='01').amount, Decimal('30.00'))

    def test_insufficient_cash_does_not_allocate(self):
        self.sale(date(2026, 1, 5), 1, '10.00')
        expense = Out.objects.create(description='Achat', amount=Decimal('11.00'), date=date(2026, 1, 20))
        with self.assertRaises(ValidationError):
            allocate_expense(expense)
        self.assertFalse(OutAllocation.objects.filter(out=expense).exists())
