"""
Django models for the CCL Reservation System
"""
import datetime
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils.html import format_html

from .constants import WEEKDAY_CHOICES


class FoodItem(models.Model):
    """
    Represents a food item that can be ordered (lunch or snacks)
    """
    LUNCH = "LUNCH"
    SNACKS = "SNACKS"
    TYPE_CHOICES = (
        (LUNCH, "Lunch"),
        (SNACKS, "Snacks")
    )

    type = models.CharField(
        max_length=10, 
        choices=TYPE_CHOICES, 
        default=LUNCH,
        help_text="Type of food item"
    )
    name = models.CharField(max_length=200, help_text="Name of the food item")
    price = models.IntegerField(default=0, help_text="Price in PHP")
    image = models.CharField(max_length=200, help_text="URL to food item image")

    class Meta:
        ordering = ['name']
        verbose_name = "Food Item"
        verbose_name_plural = "Food Items"

    def image_displayed(self):
        """Display image in Django admin with proper styling"""
        return format_html(
            '<img style="width: 125px; height:125px; object-fit: cover;" src="{}">',
            self.image,
        )
    image_displayed.short_description = 'Image Preview'

    def __str__(self):
        return f"{self.name} (₱{self.price})"


class Option(models.Model):
    """
    Represents food options available for a specific weekday
    """
    food_items = models.ManyToManyField(
        FoodItem, 
        help_text="Food items available for this day"
    )
    weekday = models.CharField(
        max_length=3, 
        choices=WEEKDAY_CHOICES,
        help_text="Day of the week"
    )

    class Meta:
        ordering = ['weekday']
        verbose_name = "Daily Option"
        verbose_name_plural = "Daily Options"

    def __str__(self):
        return f"{self.get_weekday_display().title()} Options"


class Reservation(models.Model):
    """
    Represents food reservations for a specific weekday
    """
    weekday = models.CharField(
        max_length=3, 
        choices=WEEKDAY_CHOICES,
        help_text="Day of the week for this reservation"
    )
    paid = models.BooleanField(
        default=False,
        help_text="Whether this reservation has been paid for"
    )

    class Meta:
        ordering = ['weekday']
        verbose_name = "Daily Reservation"
        verbose_name_plural = "Daily Reservations"

    def get_total_amount(self):
        """Calculate total amount for this reservation"""
        return sum(
            selection.line_total() 
            for selection in self.selection_set.all()
        )

    def __str__(self):
        return f"{self.get_weekday_display().title()} Reservation"


class Selection(models.Model):
    """
    Represents a specific food item selection within a reservation
    """
    reservation = models.ForeignKey(
        Reservation, 
        on_delete=models.CASCADE,
        help_text="The reservation this selection belongs to"
    )
    food_item = models.ForeignKey(
        FoodItem, 
        on_delete=models.CASCADE,
        help_text="The selected food item"
    )
    quantity = models.IntegerField(
        default=0,
        help_text="Number of items ordered"
    )

    class Meta:
        verbose_name = "Food Selection"
        verbose_name_plural = "Food Selections"
        unique_together = ['reservation', 'food_item']
        ordering = ['food_item__name']

    def line_total(self):
        """Calculate total cost for this selection"""
        return self.quantity * self.food_item.price

    def __str__(self):
        return f"{self.quantity}x {self.food_item.name}"


class Form(models.Model):
    """
    Base class for weekly food forms (lunch or snacks)
    """
    created_at = models.DateTimeField(
        default=datetime.datetime.now,
        help_text="When this form was created"
    )
    active = models.BooleanField(
        default=False,
        help_text="Whether this form is currently active for ordering"
    )
    week = models.CharField(
        max_length=50,
        help_text="Week identifier (e.g., 2024-W01)"
    )
    options = models.ManyToManyField(
        Option,
        help_text="Food options available for each day of the week"
    )

    class Meta:
        ordering = ['-week']
        verbose_name = "Food Form"
        verbose_name_plural = "Food Forms"

    def display_week(self):
        """Format week string for display"""
        try:
            year = int(self.week.split("-")[0])
            week = int(self.week.split("W")[-1])

            start_date = datetime.date.fromisocalendar(year, week, 1)
            end_date = start_date + timedelta(days=6)

            return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        except (ValueError, IndexError):
            return self.week
    display_week.short_description = 'Week Period'

    def display_type(self):
        """Get the type of form (lunch or snacks)"""
        if hasattr(self, 'lunchform'):
            return self.lunchform
        elif hasattr(self, 'snacksform'):
            return self.snacksform
        else:
            return 'Not specified'
    display_type.short_description = 'Form Type'

    def get_total_orders(self):
        """Get count of orders for this form"""
        return self.order_set.count()
    get_total_orders.short_description = 'Total Orders'

    def __str__(self):
        return self.display_week()


class LunchForm(Form):
    """
    Weekly lunch ordering form
    """
    type = "LUNCH"

    class Meta:
        verbose_name = "Lunch Form"
        verbose_name_plural = "Lunch Forms"

    def __str__(self):
        return f"Lunch Form "


class SnacksForm(Form):
    """
    Weekly snacks ordering form
    """
    type = "SNACKS"

    class Meta:
        verbose_name = "Snacks Form"
        verbose_name_plural = "Snacks Forms"

    def __str__(self):
        return f"Snacks Form "


class Profile(models.Model):
    """
    Extended user profile with additional information
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        help_text="Associated Django user account"
    )
    name = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Full name of the user"
    )
    role = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Job title/role"
    )
    department = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Department/division"
    )
    coins = models.IntegerField(
        default=0,
        help_text="Number of reward coins earned by the user"
    )

    class Meta:
        ordering = ['name']
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def add_coins(self, amount):
        """Add coins to the user's account"""
        self.coins += amount
        self.save()

    def get_total_orders(self):
        """Get total number of orders placed by this user"""
        return self.order_set.count()
    get_total_orders.short_description = 'Total Orders'

    def get_unpaid_orders(self):
        """Get number of unpaid orders"""
        return self.order_set.filter(paid=False).count()
    get_unpaid_orders.short_description = 'Unpaid Orders'

    def __str__(self):
        return self.name


class Order(models.Model):
    """
    Represents a complete weekly food order
    """
    reservations = models.ManyToManyField(
        Reservation, 
        related_name="order",
        help_text="Daily reservations included in this order"
    )
    form = models.ForeignKey(
        Form, 
        on_delete=models.CASCADE,
        help_text="The form this order was placed on"
    )
    profile = models.ForeignKey(
        Profile, 
        on_delete=models.CASCADE,
        help_text="User who placed this order"
    )
    paid = models.BooleanField(
        default=False,
        help_text="Whether this order has been fully paid"
    )
    total_paid = models.IntegerField(
        default=0,
        help_text="Total amount for this order in PHP"
    )
    grade = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="User's department/grade information"
    )
    name = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="User's name"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this order was created"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Food Order"
        verbose_name_plural = "Food Orders"

    def display_user(self):
        """Get user's name for display"""
        return self.profile.name
    display_user.short_description = 'User'

    def display_order_type(self):
        """Get form type for display"""
        return self.form.display_type()
    display_order_type.short_description = "Type"

    def get_reservation_count(self):
        """Get number of daily reservations in this order"""
        return self.reservations.count()
    get_reservation_count.short_description = 'Days Ordered'

    def __str__(self):
        return f"{self.profile.name} - {self.form.display_week()}"


