from django.contrib import admin
from .models import Category, Budget, Expense


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'description', 'expense_count', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['name', 'user__username', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def expense_count(self, obj):
        return obj.expenses.count()
    expense_count.short_description = 'Expenses'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['category', 'user', 'monthly_limit', 'month_year', 'created_at']
    list_filter = ['user', 'month_year', 'category']
    search_fields = ['category__name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'user', 'amount', 'date', 'notes', 'created_at']
    list_filter = ['user', 'date', 'category']
    search_fields = ['category__name', 'user__username', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
