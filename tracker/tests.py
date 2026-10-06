"""
SpendWise - Comprehensive Test Suite
Tests authentication, CRUD operations, security, calculations, and thresholds.
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import datetime

from .models import Category, Budget, Expense
from .views import calculate_budget_status


# ─── Helper ────────────────────────────────────────────────────────────────────

def make_user(username='testuser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)


def make_category(user, name='Food', description='Test'):
    return Category.objects.create(user=user, name=name, description=description)


def make_budget(user, category, monthly_limit=Decimal('1000.00'), month_year=None):
    if month_year is None:
        today = timezone.localdate()
        month_year = datetime.date(today.year, today.month, 1)
    return Budget.objects.create(
        user=user, category=category,
        monthly_limit=monthly_limit,
        month_year=month_year
    )


def make_expense(user, category, amount=Decimal('100.00'), date=None, notes=''):
    if date is None:
        date = timezone.localdate()
    return Expense.objects.create(
        user=user, category=category,
        amount=amount, date=date, notes=notes
    )


# ─── 1. Authentication Tests ────────────────────────────────────────────────────

class AuthenticationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()

    def test_1_registration_creates_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'securepass123!',
            'password2': 'securepass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_2_login_valid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_3_logout(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_4_anonymous_dashboard_redirects(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_registration_duplicate_username(self):
        response = self.client.post(reverse('register'), {
            'username': 'testuser',  # already exists
            'password1': 'securepass123!',
            'password2': 'securepass123!',
        })
        # Should return 200 with error, not create duplicate
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='testuser').count(), 1)

    def test_registration_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'anotheruser',
            'password1': 'securepass123!',
            'password2': 'differentpass!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anotheruser').exists())

    def test_anonymous_categories_redirects(self):
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_budgets_redirects(self):
        response = self.client.get(reverse('budget_list'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_expenses_redirects(self):
        response = self.client.get(reverse('expense_list'))
        self.assertEqual(response.status_code, 302)


# ─── 2. Category Tests ──────────────────────────────────────────────────────────

class CategoryTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.user2 = make_user(username='user2')
        self.client.login(username='testuser', password='testpass123')

    def test_5_create_category(self):
        response = self.client.post(reverse('category_create'), {
            'name': 'Transport',
            'description': 'Bus and taxi fares',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(user=self.user, name='Transport').exists())

    def test_6_read_category(self):
        cat = make_category(self.user)
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Food')

    def test_7_update_category(self):
        cat = make_category(self.user, name='OldName')
        response = self.client.post(reverse('category_edit', args=[cat.pk]), {
            'name': 'NewName',
            'description': 'Updated description',
        })
        self.assertEqual(response.status_code, 302)
        cat.refresh_from_db()
        self.assertEqual(cat.name, 'NewName')

    def test_8_delete_category_without_expenses(self):
        cat = make_category(self.user, name='EmptyCat')
        response = self.client.post(reverse('category_delete', args=[cat.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=cat.pk).exists())

    def test_9_cannot_delete_category_with_expenses(self):
        cat = make_category(self.user, name='UsedCat')
        make_expense(self.user, cat)
        response = self.client.post(reverse('category_delete', args=[cat.pk]))
        self.assertEqual(response.status_code, 302)
        # Category should still exist
        self.assertTrue(Category.objects.filter(pk=cat.pk).exists())

    def test_10_user_isolation_category(self):
        cat2 = make_category(self.user2, name='User2Cat')
        # user1 should not see user2's categories
        response = self.client.get(reverse('category_list'))
        self.assertNotContains(response, 'User2Cat')

    def test_duplicate_category_name_rejected(self):
        make_category(self.user, name='DupTest')
        response = self.client.post(reverse('category_create'), {
            'name': 'DupTest',
            'description': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.filter(user=self.user, name='DupTest').count(), 1)

    def test_duplicate_name_case_insensitive(self):
        make_category(self.user, name='Food')
        response = self.client.post(reverse('category_create'), {
            'name': 'food',
            'description': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.filter(user=self.user).count(), 1)


# ─── 3. Budget Tests ────────────────────────────────────────────────────────────

class BudgetTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.user2 = make_user(username='user2')
        self.cat = make_category(self.user)
        self.cat2 = make_category(self.user2, name='User2Food')
        self.client.login(username='testuser', password='testpass123')
        today = timezone.localdate()
        self.month_str = f'{today.year}-{today.month:02d}'
        self.month_first = datetime.date(today.year, today.month, 1)

    def test_11_create_budget(self):
        response = self.client.post(reverse('budget_create'), {
            'category': self.cat.pk,
            'month_year': self.month_str,
            'monthly_limit': '5000.00',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Budget.objects.filter(
            user=self.user, category=self.cat, monthly_limit=Decimal('5000.00')
        ).exists())

    def test_12_update_budget(self):
        budget = make_budget(self.user, self.cat, Decimal('1000.00'))
        response = self.client.post(reverse('budget_edit', args=[budget.pk]), {
            'category': self.cat.pk,
            'month_year': self.month_str,
            'monthly_limit': '2000.00',
        })
        self.assertEqual(response.status_code, 302)
        budget.refresh_from_db()
        self.assertEqual(budget.monthly_limit, Decimal('2000.00'))

    def test_13_delete_budget(self):
        budget = make_budget(self.user, self.cat)
        response = self.client.post(reverse('budget_delete', args=[budget.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Budget.objects.filter(pk=budget.pk).exists())

    def test_14_duplicate_budget_prevention(self):
        make_budget(self.user, self.cat)
        response = self.client.post(reverse('budget_create'), {
            'category': self.cat.pk,
            'month_year': self.month_str,
            'monthly_limit': '3000.00',
        })
        # Should fail - duplicate budget
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Budget.objects.filter(user=self.user, category=self.cat).count(), 1)

    def test_15_budget_user_isolation(self):
        budget2 = make_budget(self.user2, self.cat2)
        response = self.client.get(reverse('budget_list'))
        self.assertNotContains(response, 'User2Food')
        # user1 cannot edit user2's budget
        response = self.client.get(reverse('budget_edit', args=[budget2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_budget_zero_amount_rejected(self):
        response = self.client.post(reverse('budget_create'), {
            'category': self.cat.pk,
            'month_year': self.month_str,
            'monthly_limit': '0.00',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Budget.objects.filter(user=self.user, category=self.cat).exists())

    def test_budget_negative_amount_rejected(self):
        response = self.client.post(reverse('budget_create'), {
            'category': self.cat.pk,
            'month_year': self.month_str,
            'monthly_limit': '-500.00',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Budget.objects.filter(user=self.user, category=self.cat).exists())


# ─── 4. Expense Tests ───────────────────────────────────────────────────────────

class ExpenseTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.user2 = make_user(username='user2')
        self.cat = make_category(self.user)
        self.cat2 = make_category(self.user2, name='User2Cat')
        self.client.login(username='testuser', password='testpass123')
        self.today = timezone.localdate()

    def test_16_create_expense(self):
        response = self.client.post(reverse('expense_create'), {
            'amount': '450.00',
            'date': str(self.today),
            'category': self.cat.pk,
            'notes': 'Lunch',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(
            user=self.user, amount=Decimal('450.00')
        ).exists())

    def test_17_update_expense(self):
        exp = make_expense(self.user, self.cat, Decimal('100.00'))
        response = self.client.post(reverse('expense_edit', args=[exp.pk]), {
            'amount': '200.00',
            'date': str(self.today),
            'category': self.cat.pk,
            'notes': 'Updated',
        })
        self.assertEqual(response.status_code, 302)
        exp.refresh_from_db()
        self.assertEqual(exp.amount, Decimal('200.00'))

    def test_18_delete_expense(self):
        exp = make_expense(self.user, self.cat)
        response = self.client.post(reverse('expense_delete', args=[exp.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Expense.objects.filter(pk=exp.pk).exists())

    def test_19_negative_amount_rejected(self):
        response = self.client.post(reverse('expense_create'), {
            'amount': '-50.00',
            'date': str(self.today),
            'category': self.cat.pk,
            'notes': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Expense.objects.filter(user=self.user).exists())

    def test_20_zero_amount_rejected(self):
        response = self.client.post(reverse('expense_create'), {
            'amount': '0.00',
            'date': str(self.today),
            'category': self.cat.pk,
            'notes': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Expense.objects.filter(user=self.user).exists())

    def test_21_invalid_category_ownership_rejected(self):
        """User1 cannot create expense with User2's category"""
        response = self.client.post(reverse('expense_create'), {
            'amount': '100.00',
            'date': str(self.today),
            'category': self.cat2.pk,  # belongs to user2
            'notes': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Expense.objects.filter(user=self.user).exists())

    def test_22_expense_user_isolation(self):
        exp2 = make_expense(self.user2, self.cat2, Decimal('999.00'))
        response = self.client.get(reverse('expense_list'))
        self.assertNotContains(response, '999.00')
        # user1 cannot edit user2's expense
        response = self.client.get(reverse('expense_edit', args=[exp2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_23_post_success_returns_302(self):
        response = self.client.post(reverse('expense_create'), {
            'amount': '100.00',
            'date': str(self.today),
            'category': self.cat.pk,
            'notes': '',
        })
        self.assertEqual(response.status_code, 302)

    def test_24_post_invalid_returns_200(self):
        response = self.client.post(reverse('expense_create'), {
            'amount': '-1.00',
            'date': str(self.today),
            'category': self.cat.pk,
            'notes': '',
        })
        self.assertEqual(response.status_code, 200)

    def test_delete_with_get_not_allowed(self):
        """DELETE should require POST, not GET"""
        exp = make_expense(self.user, self.cat)
        # GET should show confirmation page, not delete
        response = self.client.get(reverse('expense_delete', args=[exp.pk]))
        self.assertEqual(response.status_code, 200)
        # Expense should still exist
        self.assertTrue(Expense.objects.filter(pk=exp.pk).exists())


# ─── 5. Calculation Tests ────────────────────────────────────────────────────────

class CalculationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.cat = make_category(self.user)
        self.client.login(username='testuser', password='testpass123')
        self.today = timezone.localdate()

    def test_25_total_monthly_spending(self):
        make_expense(self.user, self.cat, Decimal('100.00'))
        make_expense(self.user, self.cat, Decimal('200.00'))
        make_expense(self.user, self.cat, Decimal('50.00'))

        from django.db.models import Sum
        total = Expense.objects.filter(
            user=self.user,
            date__year=self.today.year,
            date__month=self.today.month
        ).aggregate(total=Sum('amount'))['total']
        self.assertEqual(total, Decimal('350.00'))

    def test_26_total_budget(self):
        cat2 = make_category(self.user, name='Transport')
        make_budget(self.user, self.cat, Decimal('1000.00'))
        make_budget(self.user, cat2, Decimal('500.00'))

        from django.db.models import Sum
        month_first = datetime.date(self.today.year, self.today.month, 1)
        total = Budget.objects.filter(
            user=self.user, month_year=month_first
        ).aggregate(total=Sum('monthly_limit'))['total']
        self.assertEqual(total, Decimal('1500.00'))

    def test_27_remaining_budget(self):
        make_budget(self.user, self.cat, Decimal('1000.00'))
        make_expense(self.user, self.cat, Decimal('300.00'))
        make_expense(self.user, self.cat, Decimal('200.00'))

        from django.db.models import Sum
        month_first = datetime.date(self.today.year, self.today.month, 1)
        total_budget = Budget.objects.filter(
            user=self.user, month_year=month_first
        ).aggregate(total=Sum('monthly_limit'))['total'] or Decimal('0')
        total_spent = Expense.objects.filter(
            user=self.user,
            date__year=self.today.year,
            date__month=self.today.month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        remaining = total_budget - total_spent
        self.assertEqual(remaining, Decimal('500.00'))

    def test_28_category_spending(self):
        cat2 = make_category(self.user, name='Transport')
        make_expense(self.user, self.cat, Decimal('100.00'))
        make_expense(self.user, self.cat, Decimal('150.00'))
        make_expense(self.user, cat2, Decimal('50.00'))

        from django.db.models import Sum
        food_spent = Expense.objects.filter(
            user=self.user, category=self.cat,
            date__year=self.today.year,
            date__month=self.today.month
        ).aggregate(total=Sum('amount'))['total']
        self.assertEqual(food_spent, Decimal('250.00'))


# ─── 6. Threshold Tests ──────────────────────────────────────────────────────────

class ThresholdTests(TestCase):

    def test_29_79_99_is_normal(self):
        result = calculate_budget_status(Decimal('7999'), Decimal('10000'))
        # 79.99% -> normal
        self.assertEqual(result['status'], 'normal')
        self.assertAlmostEqual(float(result['percentage']), 79.99, places=1)

    def test_30_80_is_warning(self):
        result = calculate_budget_status(Decimal('8000'), Decimal('10000'))
        # 80% -> warning
        self.assertEqual(result['status'], 'warning')
        self.assertAlmostEqual(float(result['percentage']), 80.0, places=1)

    def test_31_80_01_is_warning(self):
        result = calculate_budget_status(Decimal('8001'), Decimal('10000'))
        # 80.01% -> warning
        self.assertEqual(result['status'], 'warning')

    def test_32_99_99_is_warning(self):
        result = calculate_budget_status(Decimal('9999'), Decimal('10000'))
        # 99.99% -> warning
        self.assertEqual(result['status'], 'warning')

    def test_33_100_is_danger(self):
        result = calculate_budget_status(Decimal('10000'), Decimal('10000'))
        # 100% -> danger
        self.assertEqual(result['status'], 'danger')
        self.assertAlmostEqual(float(result['percentage']), 100.0, places=1)

    def test_34_100_01_is_danger(self):
        result = calculate_budget_status(Decimal('10001'), Decimal('10000'))
        # 100.01% -> danger
        self.assertEqual(result['status'], 'danger')

    def test_35_no_budget_no_division_by_zero(self):
        """No budget should not cause division by zero"""
        result = calculate_budget_status(Decimal('500'), None)
        self.assertEqual(result['status'], 'no-budget')
        self.assertEqual(result['percentage'], Decimal('0'))

    def test_35b_zero_budget_no_division_by_zero(self):
        result = calculate_budget_status(Decimal('500'), Decimal('0'))
        self.assertEqual(result['status'], 'no-budget')

    def test_threshold_labels(self):
        normal = calculate_budget_status(Decimal('500'), Decimal('1000'))
        self.assertEqual(normal['status_label'], 'On Track')

        warning = calculate_budget_status(Decimal('800'), Decimal('1000'))
        self.assertEqual(warning['status_label'], 'Near Limit')

        danger = calculate_budget_status(Decimal('1000'), Decimal('1000'))
        self.assertEqual(danger['status_label'], 'Over Budget')

        no_budget = calculate_budget_status(Decimal('500'), None)
        self.assertEqual(no_budget['status_label'], 'No Budget')

    def test_150_percent_is_danger(self):
        result = calculate_budget_status(Decimal('1500'), Decimal('1000'))
        self.assertEqual(result['status'], 'danger')
        self.assertAlmostEqual(float(result['percentage']), 150.0, places=1)

    def test_0_percent_is_normal(self):
        result = calculate_budget_status(Decimal('0'), Decimal('1000'))
        self.assertEqual(result['status'], 'normal')

    def test_remaining_calculation(self):
        result = calculate_budget_status(Decimal('700'), Decimal('1000'))
        self.assertEqual(result['remaining'], Decimal('300'))

    def test_remaining_negative_when_over_budget(self):
        result = calculate_budget_status(Decimal('1200'), Decimal('1000'))
        self.assertEqual(result['remaining'], Decimal('-200'))


# ─── 7. Security Tests ───────────────────────────────────────────────────────────

class SecurityTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_a = make_user(username='userA', password='passA1234!')
        self.user_b = make_user(username='userB', password='passB1234!')
        self.cat_b = make_category(self.user_b, name='B-Food')
        self.budget_b = make_budget(self.user_b, self.cat_b, Decimal('2000.00'))
        self.expense_b = make_expense(self.user_b, self.cat_b, Decimal('500.00'))
        self.client.login(username='userA', password='passA1234!')

    def test_36_user_a_cannot_access_user_b_category(self):
        response = self.client.get(reverse('category_edit', args=[self.cat_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_37_user_a_cannot_access_user_b_budget(self):
        response = self.client.get(reverse('budget_edit', args=[self.budget_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_38_user_a_cannot_access_user_b_expense(self):
        response = self.client.get(reverse('expense_edit', args=[self.expense_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_39_user_a_cannot_edit_user_b_expense(self):
        cat_a = make_category(self.user_a, name='A-Food')
        response = self.client.post(
            reverse('expense_edit', args=[self.expense_b.pk]),
            {
                'amount': '999.00',
                'date': str(timezone.localdate()),
                'category': cat_a.pk,
                'notes': 'Hacked',
            }
        )
        self.assertEqual(response.status_code, 404)
        self.expense_b.refresh_from_db()
        self.assertEqual(self.expense_b.amount, Decimal('500.00'))

    def test_40_user_a_cannot_delete_user_b_expense(self):
        response = self.client.post(reverse('expense_delete', args=[self.expense_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Expense.objects.filter(pk=self.expense_b.pk).exists())

    def test_user_a_cannot_delete_user_b_category(self):
        response = self.client.post(reverse('category_delete', args=[self.cat_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Category.objects.filter(pk=self.cat_b.pk).exists())

    def test_user_a_cannot_delete_user_b_budget(self):
        response = self.client.post(reverse('budget_delete', args=[self.budget_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Budget.objects.filter(pk=self.budget_b.pk).exists())

    def test_user_a_cannot_use_user_b_category_in_expense(self):
        """User A cannot create expense with User B's category"""
        response = self.client.post(reverse('expense_create'), {
            'amount': '100.00',
            'date': str(timezone.localdate()),
            'category': self.cat_b.pk,
            'notes': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Expense.objects.filter(user=self.user_a).exists())

    def test_csrf_required(self):
        """CSRF token must be present for POST requests"""
        client = Client(enforce_csrf_checks=True)
        client.login(username='userA', password='passA1234!')
        cat_a = make_category(self.user_a)
        response = client.post(reverse('expense_create'), {
            'amount': '100.00',
            'date': str(timezone.localdate()),
            'category': cat_a.pk,
            'notes': '',
        })
        self.assertEqual(response.status_code, 403)


# ─── 8. Dashboard Tests ──────────────────────────────────────────────────────────

class DashboardTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.cat = make_category(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_dashboard_loads(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_shows_correct_totals(self):
        make_budget(self.user, self.cat, Decimal('1000.00'))
        make_expense(self.user, self.cat, Decimal('300.00'))
        make_expense(self.user, self.cat, Decimal('200.00'))

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_spending', response.context)
        self.assertIn('total_budget', response.context)
        self.assertIn('remaining_budget', response.context)
        self.assertEqual(response.context['total_spending'], Decimal('500.00'))
        self.assertEqual(response.context['total_budget'], Decimal('1000.00'))
        self.assertEqual(response.context['remaining_budget'], Decimal('500.00'))

    def test_dashboard_empty_no_crash(self):
        """Dashboard must not crash when no data"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_spending'], Decimal('0.00'))
        self.assertEqual(response.context['total_budget'], Decimal('0.00'))

    def test_dashboard_only_current_month(self):
        """Expenses from other months should not appear in dashboard"""
        last_month = timezone.localdate().replace(day=1)
        if last_month.month == 1:
            last_month = last_month.replace(year=last_month.year - 1, month=12)
        else:
            last_month = last_month.replace(month=last_month.month - 1)

        make_expense(self.user, self.cat, Decimal('999.00'), date=last_month)
        make_expense(self.user, self.cat, Decimal('100.00'))

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['total_spending'], Decimal('100.00'))


# ─── 9. Model Tests ──────────────────────────────────────────────────────────────

class ModelTests(TestCase):

    def test_category_unique_per_user(self):
        user = make_user()
        make_category(user, name='UniqueTest')
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            Category.objects.create(user=user, name='UniqueTest')

    def test_budget_unique_per_user_category_month(self):
        user = make_user()
        cat = make_category(user)
        make_budget(user, cat)
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            Budget.objects.create(
                user=user, category=cat,
                monthly_limit=Decimal('500'),
                month_year=datetime.date(timezone.localdate().year, timezone.localdate().month, 1)
            )

    def test_expense_str(self):
        user = make_user()
        cat = make_category(user)
        exp = make_expense(user, cat, Decimal('250.00'))
        self.assertIn('₹', str(exp))
        self.assertIn('Food', str(exp))

    def test_category_has_expenses(self):
        user = make_user()
        cat = make_category(user)
        self.assertFalse(cat.has_expenses())
        make_expense(user, cat)
        cat.refresh_from_db()
        self.assertTrue(cat.has_expenses())

    def test_expense_amount_precision(self):
        user = make_user()
        cat = make_category(user)
        exp = make_expense(user, cat, Decimal('123.45'))
        self.assertEqual(exp.amount, Decimal('123.45'))
