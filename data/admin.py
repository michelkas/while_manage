from django.contrib import admin
from .models import Article, In, Out, OutAllocation, StockEntry


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('name', 'reference', 'price', 'quantity', 'reorder_level', 'date_added')
    search_fields = ('name',)


@admin.register(In)
class InAdmin(admin.ModelAdmin):
    list_display = ('article', 'quantity', 'unit_price', 'total_price', 'date', 'month')
    list_filter = ('month',)


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ('article', 'quantity', 'unit_cost', 'date', 'note')
    list_filter = ('date',)


class OutAllocationInline(admin.TabularInline):
    model = OutAllocation
    readonly_fields = ('month', 'year', 'amount')
    extra = 0
    can_delete = False


@admin.register(Out)
class OutAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date', 'month')
    list_filter = ('month',)
    inlines = (OutAllocationInline,)
