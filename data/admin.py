from django.contrib import admin
from .models import Article, In, Out, OutAllocation, StockEntry, WeeklyReport
from .services import delete_article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('name', 'reference', 'price', 'quantity', 'reorder_level', 'date_added')
    search_fields = ('name',)

    def get_deleted_objects(self, objs, request):
        return [str(obj) for obj in objs], {self.opts.verbose_name_plural: len(objs)}, set(), []

    def delete_model(self, request, obj):
        delete_article(obj)


@admin.register(In)
class InAdmin(admin.ModelAdmin):
    list_display = ('article', 'quantity', 'unit_price', 'total_price', 'date', 'month')
    list_filter = ('month',)


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ('article', 'quantity', 'unit_cost', 'date', 'note')
    list_filter = ('date',)


@admin.register(WeeklyReport)
class WeeklyReportAdmin(admin.ModelAdmin):
    list_display = ('week_start', 'week_end', 'income_total', 'expense_total', 'balance_total', 'generated_at')
    readonly_fields = ('week_start', 'week_end', 'income_total', 'expense_total', 'balance_total', 'generated_at')


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
