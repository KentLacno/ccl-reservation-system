"""
Service classes for handling business logic
"""
import random
import string
import base64
import requests
from requests_oauthlib import OAuth2Session
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from .models import Profile, Order, Reservation, Selection, FoodItem
from .constants import (
    MICROSOFT_OAUTH_SCOPES, ALLOWED_EMAIL_DOMAIN, RANDOM_PASSWORD_LENGTH,
    MICROSOFT_AUTH_BASE_URL, MICROSOFT_TOKEN_URL, MICROSOFT_GRAPH_USER_URL,
    PAYMONGO_CHECKOUT_URL, PAYMONGO_SERVICE_FEE_RATE, PESO_TO_CENTAVOS_MULTIPLIER,
    WEEKDAYS
)

User = get_user_model()


class MicrosoftOAuthService:
    """Handles Microsoft OAuth authentication"""
    
    def __init__(self, client_id, client_secret, host_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.host_url = host_url
    
    def get_oauth_session(self):
        """Initialize OAuth2 session"""
        redirect_uri = f"{self.host_url}callback"
        return OAuth2Session(
            self.client_id, 
            scope=MICROSOFT_OAUTH_SCOPES, 
            redirect_uri=redirect_uri
        )
    
    def get_authorization_url(self):
        """Get Microsoft authorization URL"""
        oauth = self.get_oauth_session()
        authorization_url, state = oauth.authorization_url(MICROSOFT_AUTH_BASE_URL)
        return authorization_url
    
    def get_user_info(self, authorization_code):
        """Exchange code for token and get user info"""
        oauth = self.get_oauth_session()
        token = oauth.fetch_token(
            MICROSOFT_TOKEN_URL, 
            client_secret=self.client_secret, 
            code=authorization_code
        )
        
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        response = requests.get(MICROSOFT_GRAPH_USER_URL, headers=headers)
        return response.json()


class UserService:
    """Handles user creation and authentication"""
    
    @staticmethod
    def is_allowed_email(email):
        """Check if email domain is allowed"""
        return email.split('@')[1] == ALLOWED_EMAIL_DOMAIN
    
    @staticmethod
    def create_user_from_oauth(user_data):
        """Create user and profile from OAuth data"""
        email = user_data["mail"]
        
        if not UserService.is_allowed_email(email):
            return None
            
        random_password = "".join(
            random.choice(string.ascii_letters) 
            for _ in range(RANDOM_PASSWORD_LENGTH)
        )
        
        user = User(
            username=email, 
            email=email, 
            password=make_password(random_password)
        )
        user.save()
        
        Profile.objects.create(
            user=user,
            name=user_data.get("displayName"),
            role=user_data.get("jobTitle"),
            department=user_data.get("department"),
            coins=50  # New users start with 50 coins
        )
        
        return user


class PaymentService:
    """Handles payment processing with PayMongo"""
    
    def __init__(self, secret_key, host_url):
        self.secret_key = secret_key
        self.host_url = host_url
    
    def _get_headers(self):
        """Get PayMongo API headers"""
        base64_secret = base64.b64encode(self.secret_key.encode("ascii")).decode("ascii")
        return {
            "accept": "application/json",
            "authorization": f"Basic {base64_secret}",
            "content-type": "application/json"
        }
    
    def create_checkout_session(self, amount, metadata):
        """Create PayMongo checkout session"""
        service_fee = round(amount * PESO_TO_CENTAVOS_MULTIPLIER * PAYMONGO_SERVICE_FEE_RATE)
        
        payload = {
            "data": {
                "attributes": {
                    "payment_method_types": ["gcash"],
                    "line_items": [
                        {
                            "amount": amount * PESO_TO_CENTAVOS_MULTIPLIER,
                            "currency": "PHP",
                            "name": "Total",
                            "quantity": 1
                        },
                        {
                            "amount": service_fee,
                            "currency": "PHP",
                            "name": "Small Service Fee",
                            "quantity": 1
                        }
                    ],
                    "description": "Food Reservation Payment",
                    "send_email_receipt": False,
                    "show_description": True,
                    "show_line_items": True,
                    "success_url": self.host_url,
                    "metadata": metadata
                }
            }
        }
        
        response = requests.post(
            PAYMONGO_CHECKOUT_URL, 
            json=payload, 
            headers=self._get_headers()
        )
        return response.json()


class OrderService:
    """Handles order creation and management"""
    
    @staticmethod
    def create_order_from_form_data(form_data, active_form, profile):
        """Create order from form submission data"""
        order = Order.objects.create(
            form=active_form, 
            profile=profile,
            grade=profile.department or "Unknown",  # Use profile's department as grade
            name=profile.name    # Use profile's name
        )
        total_paid = 0
        
        # Group food items by weekday
        food_items_by_weekday = OrderService._group_food_items_by_weekday(form_data)
        
        # Create reservations for each weekday
        for weekday_num, food_items in food_items_by_weekday.items():
            if food_items:  # Only create reservation if there are items
                reservation = Reservation.objects.create(weekday=weekday_num)
                
                for food_item_data in food_items:
                    food_item = FoodItem.objects.get(id=food_item_data["food_item_id"])
                    quantity = int(food_item_data["quantity"])
                    total_paid += food_item.price * quantity
                    
                    Selection.objects.create(
                        reservation=reservation,
                        food_item=food_item,
                        quantity=quantity
                    )
                
                order.reservations.add(reservation)
        
        order.total_paid = total_paid
        order.save()
        
        # Award coins based on total spent (20 coins for every 50 PHP)
        total_coins = (total_paid // 50) * 20
        if total_coins > 0:
            profile.add_coins(total_coins)
        
        return order
    
    @staticmethod
    def _group_food_items_by_weekday(form_data):
        """Group food items by weekday from form data"""
        food_items_dict = {"1": [], "2": [], "3": [], "4": [], "5": []}
        
        for key, value in form_data.items():
            if "quantity" in key and int(value) != 0:
                food_item_id, weekday_num, *rest = key.split("-")
                food_items_dict[weekday_num].append({
                    "food_item_id": food_item_id, 
                    "quantity": value
                })
        
        return food_items_dict


class ReportService:
    """Handles report generation for admin"""
    
    @staticmethod
    def generate_quantity_report(form):
        """Generate quantity report for food preparation"""
        orders = Order.objects.filter(form=form)
        count = {
            "monday": {},
            "tuesday": {},
            "wednesday": {},
            "thursday": {},
            "friday": {},
            "total": {}
        }
        
        # Initialize counts
        for option in form.options.all():
            weekday_name = WEEKDAYS[option.weekday]
            for food_item in option.food_items.all():
                count[weekday_name][food_item.name] = 0
                if food_item.name not in count["total"]:
                    count["total"][food_item.name] = 0
        
        # Count actual orders
        for order in orders:
            for reservation in order.reservations.all():
                weekday_name = WEEKDAYS[reservation.weekday]
                for selection in reservation.selection_set.all():
                    count[weekday_name][selection.food_item.name] += selection.quantity
                    count["total"][selection.food_item.name] += selection.quantity
        
        return count
    
    @staticmethod
    def organize_orders_by_weekday(orders):
        """Organize orders by weekday for display"""
        display = {
            "monday": [],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": []
        }
        
        for order in orders:
            for reservation in order.reservations.all():
                weekday_name = WEEKDAYS[reservation.weekday]
                display[weekday_name].append(reservation)
        
        return display 