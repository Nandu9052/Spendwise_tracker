# SpendWise 💰
### Personal Expense Tracker & Smart Budget Alerts

> "Take control of your money."

SpendWise is a full-featured personal finance management web application built with Django. It enables authenticated users to track expenses, set monthly budgets, and receive smart visual alerts when approaching or exceeding their spending limits.

---

## ✨ Features

### Core Functionality
- **User Registration & Authentication** — Secure signup, login, logout
- **Category Management** — Create, edit, delete spending categories
- **Monthly Budget Setting** — Set per-category monthly spending limits
- **Expense Tracking** — Add, edit, delete expenses with date, category, notes
- **Dashboard** — Real-time financial overview for the current month

### Smart Budget Alerts
- **On Track** (< 80% used) — Green indicator
- **Near Limit** (≥ 80% and < 100% used) — Amber warning
- **Over Budget** (≥ 100% used) — Red danger alert

### Analytics & Visualization
- Doughnut chart for category-wise spending
- Progress bars for budget utilization
- KPI cards for key financial metrics
- Recent transactions list

### Security
- Complete user data isolation
- CSRF protection on all forms
- Server-side ownership validation
- Password hashing via Django auth
- POST-only deletion

---

## 📸 Screenshots

> _(Add screenshots here after running the application)_

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Django 4.2 |
| Database | SQLite (Django ORM) |
| Frontend | Django Templates, HTML5, CSS3 |
| UI Framework | Bootstrap 5.3 |
| Icons | Bootstrap Icons 1.11 |
| Charts | Chart.js 4.4 (CDN) |
| Fonts | Inter (Google Fonts) |

---

## 🏗 Architecture

```
spendwise/          ← Django project configuration
tracker/            ← Main application
  models.py         ← Category, Budget, Expense models
  views.py          ← All views + business logic
  forms.py          ← ModelForms with validation
  urls.py           ← URL patterns
  admin.py          ← Admin configuration
  tests.py          ← Comprehensive test suite
  templates/        ← Django templates
  static/           ← CSS + JS assets
```

---

## 📂 Project Structure

```
expense_tracker/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── spendwise/              ← Django config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
└── tracker/                ← Main app
    ├── models.py
    ├── views.py
    ├── forms.py
    ├── urls.py
    ├── admin.py
    ├── tests.py
    ├── migrations/
    ├── templates/
    │   └── tracker/
    │       ├── base.html
    │       ├── dashboard.html
    │       ├── login.html
    │       ├── register.html
    │       ├── categories/
    │       ├── budgets/
    │       ├── expenses/
    │       └── includes/
    └── static/
        └── tracker/
            ├── css/style.css
            └── js/app.js
```

---

## 🗄 Database Models

### Category
| Field | Type | Description |
|-------|------|-------------|
| user | ForeignKey(User) | Owner |
| name | CharField(100) | Category name (unique per user) |
| description | TextField | Optional description |
| created_at | DateTimeField | Auto timestamp |

### Budget
| Field | Type | Description |
|-------|------|-------------|
| user | ForeignKey(User) | Owner |
| category | ForeignKey(Category) | Budget category |
| monthly_limit | DecimalField(12,2) | Spending limit |
| month_year | DateField | First day of target month |

**Constraint:** Unique per (user, category, month_year)

### Expense
| Field | Type | Description |
|-------|------|-------------|
| user | ForeignKey(User) | Owner |
| category | ForeignKey(Category) | Expense category |
| amount | DecimalField(12,2) | Must be > 0 |
| date | DateField | Expense date |
| notes | TextField | Optional notes |

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/spendwise.git
cd spendwise
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create superuser (optional)
```bash
python manage.py createsuperuser
```

### 6. Run development server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

---

## 🧪 Running Tests

```bash
python manage.py test tracker
```

### Test Coverage
- Authentication (register, login, logout, anonymous access)
- Category CRUD + ownership protection + duplicate prevention
- Budget CRUD + duplicate prevention + validation
- Expense CRUD + amount validation + category ownership
- Security (cross-user isolation, CSRF)
- Budget calculations (total, remaining, category)
- Alert thresholds (79.99%, 80%, 100%, 100.01%, 150%)
- Division by zero protection

---

## 🔐 Authentication

| URL | Description |
|-----|-------------|
| `/register/` | Create new account |
| `/login/` | Sign in |
| `/logout/` | Sign out |
| `/dashboard/` | Protected — requires login |

Configured in `settings.py`:
```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
```

---

## 📊 Budget Alert Threshold Logic

```python
def calculate_budget_status(spent, budget_limit):
    percentage = (spent / budget_limit) * 100

    if percentage >= 100:
        status = 'danger'    # Over Budget
    elif percentage >= 80:
        status = 'warning'   # Near Limit
    else:
        status = 'normal'    # On Track
```

| Usage | Status | Label |
|-------|--------|-------|
| < 80% | normal | On Track |
| ≥ 80% and < 100% | warning | Near Limit |
| ≥ 100% | danger | Over Budget |
| No budget set | no-budget | No Budget |

**Exact threshold examples:**
- 79.99% → On Track
- 80.00% → Near Limit
- 80.01% → Near Limit
- 99.99% → Near Limit
- 100.00% → Over Budget
- 100.01% → Over Budget
- 150.00% → Over Budget

---

## 🔒 Security Implementation

1. **CSRF Protection** — All POST forms include `{% csrf_token %}`
2. **Login Required** — All views decorated with `@login_required`
3. **User Isolation** — Every query filtered by `user=request.user`
4. **Ownership Validation** — Object fetched with `get_object_or_404(..., user=request.user)`
5. **Category Ownership in Forms** — Queryset restricted to `Category.objects.filter(user=user)`
6. **POST-only Deletion** — DELETE actions only processed on POST
7. **Amount Validation** — Amounts must be > 0 (server-side)
8. **Password Hashing** — Django's built-in PBKDF2 hashing

---

## 🌐 URL Reference

| URL | Name | Description |
|-----|------|-------------|
| `/` | root | Redirect to dashboard or login |
| `/dashboard/` | dashboard | Main dashboard |
| `/register/` | register | User registration |
| `/login/` | login | User login |
| `/logout/` | logout | User logout |
| `/categories/` | category_list | List categories |
| `/categories/create/` | category_create | Create category |
| `/categories/<pk>/edit/` | category_edit | Edit category |
| `/categories/<pk>/delete/` | category_delete | Delete category |
| `/budgets/` | budget_list | List budgets |
| `/budgets/create/` | budget_create | Create budget |
| `/budgets/<pk>/edit/` | budget_edit | Edit budget |
| `/budgets/<pk>/delete/` | budget_delete | Delete budget |
| `/expenses/` | expense_list | List expenses |
| `/expenses/create/` | expense_create | Create expense |
| `/expenses/<pk>/edit/` | expense_edit | Edit expense |
| `/expenses/<pk>/delete/` | expense_delete | Delete expense |

---

## 🔮 Future Improvements

- Export to CSV/PDF
- Email alerts when budget exceeds threshold
- Income tracking
- Multi-currency support
- Recurring expense templates
- Yearly analytics
- Mobile app (PWA)
- Dark mode

---

## 📄 License

MIT License — Open Source

---

Built with ❤️ for the SVCET Hackathon
