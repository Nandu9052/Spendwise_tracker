from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.db import IntegrityError
from decimal import Decimal
import datetime
import json

from .models import Category, Budget, Expense
from .forms import RegistrationForm, CategoryForm, BudgetForm, ExpenseForm


# ─── Business Logic ────────────────────────────────────────────────────────────

def calculate_budget_status(spent, budget_limit):
    """
    Calculate budget status given spent and budget_limit (Decimal values).
    Returns dict with percentage, remaining, status, status_label.
    """
    if budget_limit is None or budget_limit <= Decimal('0'):
        return {
            'percentage': Decimal('0'),
            'remaining': Decimal('0'),
            'status': 'no-budget',
            'status_label': 'No Budget',
        }

    remaining = budget_limit - spent
    percentage = (spent / budget_limit) * Decimal('100')

    if percentage >= Decimal('100'):
        status = 'danger'
        status_label = 'Over Budget'
    elif percentage >= Decimal('80'):
        status = 'warning'
        status_label = 'Near Limit'
    else:
        status = 'normal'
        status_label = 'On Track'

    return {
        'percentage': percentage,
        'remaining': remaining,
        'status': status,
        'status_label': status_label,
    }


def get_month_range(year, month):
    """Return (month_start, month_end) date objects for a given year/month."""
    month_start = datetime.date(year, month, 1)
    if month == 12:
        month_end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        month_end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    return month_start, month_end


def get_category_icon(name):
    """Return Bootstrap icon class based on category name."""
    name_lower = name.lower()
    icon_map = {
        'food': 'bi-cup-hot',
        'meal': 'bi-cup-hot',
        'restaurant': 'bi-cup-hot',
        'groceries': 'bi-cart3',
        'grocery': 'bi-cart3',
        'transport': 'bi-car-front',
        'transportation': 'bi-car-front',
        'travel': 'bi-airplane',
        'shopping': 'bi-bag',
        'clothes': 'bi-bag',
        'entertainment': 'bi-controller',
        'games': 'bi-controller',
        'bills': 'bi-receipt',
        'utilities': 'bi-lightning-charge',
        'electricity': 'bi-lightning-charge',
        'health': 'bi-heart-pulse',
        'medical': 'bi-heart-pulse',
        'fitness': 'bi-heart-pulse',
        'education': 'bi-book',
        'study': 'bi-book',
        'rent': 'bi-house',
        'home': 'bi-house',
        'housing': 'bi-house',
        'salary': 'bi-cash-stack',
        'investment': 'bi-graph-up-arrow',
        'savings': 'bi-piggy-bank',
        'insurance': 'bi-shield-check',
        'subscriptions': 'bi-credit-card',
        'subscription': 'bi-credit-card',
        'fuel': 'bi-fuel-pump',
        'petrol': 'bi-fuel-pump',
        'mobile': 'bi-phone',
        'phone': 'bi-phone',
        'internet': 'bi-wifi',
        'coffee': 'bi-cup-hot',
        'cafe': 'bi-cup-hot',
        'gifts': 'bi-gift',
        'gift': 'bi-gift',
        'personal': 'bi-person',
        'social': 'bi-people',
        'pets': 'bi-activity',
        'sport': 'bi-trophy',
        'sports': 'bi-trophy',
    }
    for keyword, icon in icon_map.items():
        if keyword in name_lower:
            return icon
    return 'bi-wallet2'


# ─── Authentication Views ───────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to SpendWise, {user.username}! Your account has been created.')
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('login')
    return redirect('dashboard')


# ─── Dashboard View ─────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today = timezone.localdate()
    year, month = today.year, today.month
    month_start, month_end = get_month_range(year, month)

    # Current month expenses
    monthly_expenses = Expense.objects.filter(
        user=request.user,
        date__gte=month_start,
        date__lte=month_end
    ).select_related('category')

    total_spending = monthly_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    transaction_count = monthly_expenses.count()

    # Current month budgets
    month_first = datetime.date(year, month, 1)
    monthly_budgets = Budget.objects.filter(
        user=request.user,
        month_year=month_first
    ).select_related('category')

    total_budget = monthly_budgets.aggregate(total=Sum('monthly_limit'))['total'] or Decimal('0.00')
    remaining_budget = total_budget - total_spending

    # Overall usage
    if total_budget > Decimal('0'):
        overall_percentage = (total_spending / total_budget) * Decimal('100')
    else:
        overall_percentage = Decimal('0')

    # Category-wise spending with budget health
    categories = Category.objects.filter(user=request.user)
    category_data = []
    chart_labels = []
    chart_values = []
    chart_colors = []

    color_palette = [
        '#4361ee', '#7209b7', '#f72585', '#4cc9f0', '#06d6a0',
        '#ffd166', '#ef476f', '#118ab2', '#073b4c', '#a8dadc'
    ]

    for i, cat in enumerate(categories):
        # Spending for this category this month
        cat_spent = monthly_expenses.filter(category=cat).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # Budget for this category this month
        try:
            cat_budget = monthly_budgets.get(category=cat)
            budget_limit = cat_budget.monthly_limit
        except Budget.DoesNotExist:
            budget_limit = None

        status_info = calculate_budget_status(cat_spent, budget_limit)
        icon = get_category_icon(cat.name)

        category_data.append({
            'category': cat,
            'spent': cat_spent,
            'budget': budget_limit,
            'icon': icon,
            **status_info,
        })

        if cat_spent > Decimal('0'):
            chart_labels.append(cat.name)
            chart_values.append(float(cat_spent))
            chart_colors.append(color_palette[i % len(color_palette)])

    # Recent transactions
    recent_expenses = monthly_expenses.order_by('-date', '-created_at')[:10]
    recent_with_icons = [
        {'expense': e, 'icon': get_category_icon(e.category.name)}
        for e in recent_expenses
    ]

    # Overall budget status
    overall_status = calculate_budget_status(total_spending, total_budget)

    # Greeting
    hour = today.timetuple().tm_hour if hasattr(today, 'timetuple') else datetime.datetime.now().hour
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = 'Good morning'
    elif hour < 17:
        greeting = 'Good afternoon'
    else:
        greeting = 'Good evening'

    context = {
        'greeting': greeting,
        'today': today,
        'month_name': today.strftime('%B %Y'),
        'total_spending': total_spending,
        'total_budget': total_budget,
        'remaining_budget': remaining_budget,
        'transaction_count': transaction_count,
        'overall_percentage': overall_percentage,
        'overall_status': overall_status,
        'category_data': category_data,
        'recent_expenses': recent_with_icons,
        # JSON-serialized for safe embedding in HTML data attributes
        'chart_labels_json': json.dumps(chart_labels),
        'chart_values_json': json.dumps(chart_values),
        'chart_colors_json': json.dumps(chart_colors),
        'has_categories': categories.exists(),
    }
    return render(request, 'tracker/dashboard.html', context)


# ─── Category Views ─────────────────────────────────────────────────────────────

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    cat_data = []
    today = timezone.localdate()
    month_first = datetime.date(today.year, today.month, 1)

    for cat in categories:
        expense_count = cat.expenses.count()
        try:
            budget = Budget.objects.get(user=request.user, category=cat, month_year=month_first)
            budget_amount = budget.monthly_limit
        except Budget.DoesNotExist:
            budget_amount = None

        cat_data.append({
            'category': cat,
            'expense_count': expense_count,
            'budget': budget_amount,
            'icon': get_category_icon(cat.name),
        })

    return render(request, 'tracker/categories/list.html', {
        'categories': cat_data,
    })


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(user=request.user)
    return render(request, 'tracker/categories/form.html', {
        'form': form,
        'title': 'Create Category',
        'subtitle': 'Add a new spending category.',
        'button_text': 'Create Category',
        'is_edit': False,
    })


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category, user=request.user)
    return render(request, 'tracker/categories/form.html', {
        'form': form,
        'category': category,
        'title': 'Edit Category',
        'subtitle': 'Update your category details.',
        'button_text': 'Save Changes',
        'is_edit': True,
    })


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        if category.has_expenses():
            messages.error(
                request,
                f'"{category.name}" cannot be deleted because it has associated expenses. '
                'Please delete or reassign those expenses first.'
            )
            return redirect('category_list')
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
        return redirect('category_list')
    return render(request, 'tracker/categories/confirm_delete.html', {
        'category': category,
        'expense_count': category.expense_count(),
    })


# ─── Budget Views ────────────────────────────────────────────────────────────────

@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).select_related('category').order_by('-month_year', 'category__name')

    today = timezone.localdate()
    month_start, month_end = get_month_range(today.year, today.month)

    budget_data = []
    for budget in budgets:
        # Calculate spending for this budget's month
        b_year = budget.month_year.year
        b_month = budget.month_year.month
        b_start, b_end = get_month_range(b_year, b_month)

        cat_spent = Expense.objects.filter(
            user=request.user,
            category=budget.category,
            date__gte=b_start,
            date__lte=b_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        status_info = calculate_budget_status(cat_spent, budget.monthly_limit)

        budget_data.append({
            'budget': budget,
            'spent': cat_spent,
            'icon': get_category_icon(budget.category.name),
            **status_info,
        })

    return render(request, 'tracker/budgets/list.html', {
        'budget_data': budget_data,
        'today': today,
        'has_categories': Category.objects.filter(user=request.user).exists(),
    })


@login_required
def budget_create(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(
                request,
                f'Budget for "{budget.category.name}" set to ₹{budget.monthly_limit:,.2f} for {budget.month_year.strftime("%B %Y")}!'
            )
            return redirect('budget_list')
    else:
        form = BudgetForm(user=request.user)
        # Default month to current
        today = timezone.localdate()
        form.fields['month_year'].initial = today.strftime('%Y-%m')
    return render(request, 'tracker/budgets/form.html', {
        'form': form,
        'title': 'Set Budget',
        'subtitle': 'Set a monthly spending limit for a category.',
        'button_text': 'Set Budget',
        'is_edit': False,
    })


@login_required
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Budget updated successfully!')
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget, user=request.user)
        # Initial is set in form __init__ already
    return render(request, 'tracker/budgets/form.html', {
        'form': form,
        'budget': budget,
        'title': 'Edit Budget',
        'subtitle': 'Update your monthly spending limit.',
        'button_text': 'Save Changes',
        'is_edit': True,
    })


@login_required
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        name = f"{budget.category.name} ({budget.month_year.strftime('%B %Y')})"
        budget.delete()
        messages.success(request, f'Budget for {name} deleted successfully!')
        return redirect('budget_list')
    return render(request, 'tracker/budgets/confirm_delete.html', {'budget': budget})


# ─── Expense Views ───────────────────────────────────────────────────────────────

@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).select_related('category')

    # Filtering
    today = timezone.localdate()
    selected_month = request.GET.get('month', today.strftime('%Y-%m'))
    selected_category = request.GET.get('category', '')
    search_query = request.GET.get('q', '')

    try:
        filter_year, filter_month = map(int, selected_month.split('-'))
        month_start, month_end = get_month_range(filter_year, filter_month)
        expenses = expenses.filter(date__gte=month_start, date__lte=month_end)
    except (ValueError, AttributeError):
        filter_year, filter_month = today.year, today.month
        month_start, month_end = get_month_range(filter_year, filter_month)
        expenses = expenses.filter(date__gte=month_start, date__lte=month_end)

    if selected_category:
        try:
            cat_id = int(selected_category)
            expenses = expenses.filter(category__id=cat_id, category__user=request.user)
        except (ValueError, TypeError):
            pass

    if search_query:
        expenses = expenses.filter(notes__icontains=search_query)

    total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    count = expenses.count()
    avg = (total / count) if count > 0 else Decimal('0.00')

    expense_with_icons = [
        {'expense': e, 'icon': get_category_icon(e.category.name)}
        for e in expenses
    ]

    user_categories = Category.objects.filter(user=request.user)

    # Build month options (last 12 months)
    month_options = []
    for i in range(12):
        d = today.replace(day=1)
        months_back = i
        y = d.year
        m = d.month - months_back
        while m <= 0:
            m += 12
            y -= 1
        month_options.append({
            'value': f'{y:04d}-{m:02d}',
            'label': datetime.date(y, m, 1).strftime('%B %Y'),
        })

    return render(request, 'tracker/expenses/list.html', {
        'expenses': expense_with_icons,
        'total': total,
        'count': count,
        'avg': avg,
        'user_categories': user_categories,
        'selected_month': selected_month,
        'selected_category': selected_category,
        'search_query': search_query,
        'month_options': month_options,
        'filter_month_label': datetime.date(filter_year, filter_month, 1).strftime('%B %Y'),
    })


@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, f'Expense of ₹{expense.amount:,.2f} added successfully!')
            return redirect('dashboard')
        # Invalid: return 200 with errors
        return render(request, 'tracker/expenses/form.html', {
            'form': form,
            'title': 'Add Expense',
            'subtitle': 'Record a new transaction.',
            'button_text': 'Save Expense',
            'is_edit': False,
        }, status=200)
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'tracker/expenses/form.html', {
        'form': form,
        'title': 'Add Expense',
        'subtitle': 'Record a new transaction.',
        'button_text': 'Save Expense',
        'is_edit': False,
    })


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    return render(request, 'tracker/expenses/form.html', {
        'form': form,
        'expense': expense,
        'title': 'Edit Expense',
        'subtitle': 'Update your transaction details.',
        'button_text': 'Save Changes',
        'is_edit': True,
    })


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        amount = expense.amount
        cat_name = expense.category.name
        expense.delete()
        messages.success(request, f'Expense of ₹{amount:,.2f} from "{cat_name}" deleted.')
        return redirect('expense_list')
    return render(request, 'tracker/expenses/confirm_delete.html', {
        'expense': expense,
        'icon': get_category_icon(expense.category.name),
    })
