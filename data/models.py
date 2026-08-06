import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class MonthChoice(models.TextChoices):
    JANUARY = '01', 'Janvier'
    FEBRUARY = '02', 'Février'
    MARCH = '03', 'Mars'
    APRIL = '04', 'Avril'
    MAY = '05', 'Mai'
    JUNE = '06', 'Juin'
    JULY = '07', 'Juillet'
    AUGUST = '08', 'Août'
    SEPTEMBER = '09', 'Septembre'
    OCTOBER = '10', 'Octobre'
    NOVEMBER = '11', 'Novembre'
    DECEMBER = '12', 'Décembre'

class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nom de l'article",max_length=255)
    description = models.TextField()
    reference = models.CharField("Référence",max_length=40, blank=True, unique=True, null=True)
    price = models.DecimalField("Prix unitaire",max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Quantité en stock")
    reorder_level = models.PositiveIntegerField("Niveau de réapprovisionnement", default=5)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

    def __str__(self):
        return self.name

    @property
    def needs_restock(self):
        return self.quantity <= self.reorder_level


class StockEntry(models.Model):
    """Une réception de marchandise, qui augmente le stock sans modifier les ventes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(Article, on_delete=models.PROTECT, related_name='stock_entries')
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Réapprovisionnement'
        verbose_name_plural = 'Réapprovisionnements'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.article} +{self.quantity}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        self.full_clean()
        super().save(*args, **kwargs)
        if creating:
            Article.objects.filter(pk=self.article_id).update(quantity=models.F('quantity') + self.quantity, price=self.unit_cost)

class In(models.Model):
    """Une vente : elle constitue une entrée d'argent pour son mois."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    month = models.CharField(max_length=2, choices=MonthChoice.choices, editable=False)

    class Meta:
        verbose_name = 'Entrée'
        verbose_name_plural = 'Entrées'
        ordering = ['-date', '-id']

    def __str__(self):
        return f"Vente {self.article} — {self.total_price}"

    def clean(self):
        if self.article_id and self.quantity and self._state.adding and self.quantity > self.article.quantity:
            raise ValidationError({'quantity': "Stock insuffisant pour cette vente."})

    def save(self, *args, **kwargs):
        self.month = f'{self.date.month:02d}'
        self.total_price = Decimal(self.quantity) * self.unit_price
        self.full_clean()
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating:
            Article.objects.filter(pk=self.article_id).update(quantity=models.F('quantity') - self.quantity)


class Out(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    month = models.CharField(max_length=2, choices=MonthChoice.choices, editable=False)

    class Meta:
        verbose_name = 'Sortie'
        verbose_name_plural = 'Sorties'
        ordering = ['-date', '-id']

    def save(self, *args, **kwargs):
        self.month = f'{self.date.month:02d}'
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} — {self.amount}"


class OutAllocation(models.Model):
    """Part d'une dépense imputée à une entrée mensuelle précise."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    out = models.ForeignKey(Out, on_delete=models.CASCADE, related_name='allocations')
    month = models.CharField(max_length=2, choices=MonthChoice.choices)
    year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Imputation de dépense'
        verbose_name_plural = 'Imputations de dépenses'
        constraints = [
            models.UniqueConstraint(fields=['out', 'month', 'year'], name='unique_out_month_allocation'),
        ]

    def __str__(self):
        return f"{self.out.description} — {self.amount} ({self.month} {self.year})"


class WeeklyReport(models.Model):
    """Clôture d'une semaine terminée, calculée depuis les opérations enregistrées."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    week_start = models.DateField(unique=True)
    week_end = models.DateField()
    income_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    expense_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rapport hebdomadaire'
        verbose_name_plural = 'Rapports hebdomadaires'
        ordering = ['-week_start']

    def __str__(self):
        return f"Semaine du {self.week_start:%d/%m/%Y}"
