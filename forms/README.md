# Forms App - CCL Reservation System

This Django app handles the core functionality of the CCL CentrEx food reservation system.

## 📁 File Structure

```
forms/
├── __init__.py
├── README.md              # This documentation
├── apps.py               # Django app configuration
├── constants.py          # Application constants and configurations
├── services.py           # Business logic services
├── models.py            # Database models
├── views.py             # HTTP request handlers
├── admin.py             # Django admin configuration
├── urls.py              # URL routing
├── forms.py             # Django forms (minimal usage)
├── tests.py             # Unit tests
├── migrations/          # Database migrations
└── templates/           # HTML templates
    ├── forms/           # User-facing templates
    └── admin/           # Admin-specific templates
```

## 🏗️ Architecture Overview

### **Separation of Concerns**

1. **`constants.py`** - All magic strings, numbers, and configuration constants
2. **`services.py`** - Business logic separated into service classes
3. **`models.py`** - Database schema and model methods
4. **`views.py`** - HTTP handling, delegating business logic to services
5. **`admin.py`** - Django admin interface configuration

### **Service Classes**

- **`MicrosoftOAuthService`** - Handles Microsoft OAuth authentication
- **`UserService`** - User creation and management
- **`PaymentService`** - PayMongo payment processing
- **`OrderService`** - Order creation and management
- **`ReportService`** - Report generation for admins

## 📊 Data Models

### **Core Models**

```python
FoodItem        # Individual food items (lunch/snacks)
├── name        # Food name
├── price       # Price in PHP
├── type        # LUNCH or SNACKS
└── image       # Image URL

Option          # Daily food options
├── weekday     # Day of week (1-5)
└── food_items  # Available food items

Form            # Weekly ordering forms
├── week        # Week identifier (2024-W01)
├── active      # Currently accepting orders
└── options     # Daily options (Mon-Fri)

Profile         # Extended user information
├── user        # Django User
├── name        # Full name
├── role        # Job title
└── department  # Department

Order           # Complete weekly food order
├── profile     # Who placed the order
├── form        # Which form/week
├── total_paid  # Total amount
├── paid        # Payment status
└── reservations # Daily reservations

Reservation     # Single day's food selections
├── weekday     # Day of week
├── paid        # Payment status
└── selections  # Food items + quantities

Selection       # Individual food item selection
├── food_item   # What food
├── quantity    # How many
└── reservation # Which day
```

### **Model Relationships**

```
User ← Profile ← Order → Form
                   ↓
              Reservation → Selection → FoodItem
                   ↑
              Option ← Form
                ↓
            FoodItem
```

## 🔄 Application Flow

### **1. Admin Setup**
1. Create food items (lunch/snacks)
2. Create weekly forms (lunch/snacks)
3. Assign food items to each weekday
4. Activate forms for user ordering

### **2. User Journey**
1. Login via Microsoft OAuth
2. View active forms and daily menus
3. Select food items and quantities
4. Submit weekly order
5. Pay via PayMongo (GCash)

### **3. Payment Processing**
1. User initiates payment
2. PayMongo creates checkout session
3. User pays via GCash
4. Webhook confirms payment
5. Order status updated

## 🛠️ Key Features

### **Authentication**
- Microsoft OAuth integration
- Organization email domain restriction (`@cclcentrex.edu.ph`)
- Automatic user profile creation

### **Ordering System**
- Weekly-based ordering
- Separate lunch and snacks forms
- Daily menu configuration
- Quantity-based selections

### **Payment Integration**
- PayMongo API integration
- GCash payment method
- Webhook-based confirmation
- Service fee calculation

### **Admin Features**
- Kitchen preparation reports
- Quantity summaries
- Order management
- Payment tracking

## 🔧 Configuration

### **Environment Variables**
```bash
PAYMONGO_SECRET_KEY=sk_test_...
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
HOST_URL=http://localhost:8000/
```

### **Constants**
All configurable values are in `constants.py`:
- Weekday mappings
- Payment fee rates
- OAuth scopes
- API endpoints
- Domain restrictions

## 🎯 Usage Examples

### **Creating a Service Instance**
```python
from .services import OrderService

# Create order from form data
order = OrderService.create_order_from_form_data(
    form_data=request.POST.dict(),
    active_form=lunch_form,
    profile=user_profile
)
```

### **Using Constants**
```python
from .constants import WEEKDAYS, PAYMONGO_SERVICE_FEE_RATE

# Get weekday name
weekday_name = WEEKDAYS["1"]  # "monday"

# Calculate service fee
fee = amount * PAYMONGO_SERVICE_FEE_RATE
```

### **Admin Actions**
```python
# Print orders for kitchen
print_orders(modeladmin, request, queryset)

# Check quantities needed
check_quantities(modeladmin, request, queryset)

# Mark orders as paid
set_paid(modeladmin, request, queryset)
```

## 🧪 Testing

Run tests with:
```bash
python manage.py test forms
```

## 📝 Development Guidelines

### **Adding New Features**
1. Add constants to `constants.py`
2. Create service methods in `services.py`
3. Update models if needed
4. Create/update views to use services
5. Update admin if needed
6. Add tests

### **Code Style**
- Use docstrings for all classes and methods
- Follow PEP 8 style guidelines
- Keep business logic in services
- Use constants instead of magic strings/numbers
- Add proper error handling

### **Security Considerations**
- All payment handling goes through services
- User authentication via OAuth only
- Domain restriction for user registration
- CSRF protection on forms
- Environment variables for sensitive data

## 🔍 Troubleshooting

### **Common Issues**

1. **Environment Variables Not Set**
   - Check `.env` file in `reservationsystem/`
   - Ensure all required variables are present

2. **OAuth Not Working**
   - Verify Microsoft app registration
   - Check redirect URI configuration
   - Confirm client ID/secret are correct

3. **Payment Issues**
   - Verify PayMongo API keys
   - Check webhook endpoint configuration
   - Ensure proper HTTPS for production

4. **Database Issues**
   - Run migrations: `python manage.py migrate`
   - Check MySQL connection settings
   - Verify database exists

## 📚 Related Documentation

- [Django Documentation](https://docs.djangoproject.com/)
- [PayMongo API Docs](https://developers.paymongo.com/)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/) 