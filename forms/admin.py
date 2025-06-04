"""
Django admin configuration for the CCL Reservation System
"""
from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import (
    FoodItem, Option, LunchForm, SnacksForm, 
    Profile, Order, Reservation, Selection
)
from .constants import WEEKDAYS


class DateInput(forms.DateInput):
    """Custom date input widget for week selection"""
    input_type = 'week'


class FormAdminArea(admin.AdminSite):
    """Custom admin site for the reservation system"""
    site_header = "CCL Reservation System Admin"
    site_title = "CCL Reservation Admin"
    index_title = "Reservation System Administration"


form_site = FormAdminArea(name="FormAdmin")


class BaseWeeklyForm(forms.ModelForm):
    """
    Base form class for weekly forms (lunch/snacks) to reduce code duplication
    """
    
    def __init__(self, *args, **kwargs):
        super(BaseWeeklyForm, self).__init__(*args, **kwargs)
        
        # Initialize weekday fields with proper food type filtering
        for weekday_name in WEEKDAYS.values():
            field_name = weekday_name
            self.fields[field_name] = forms.ModelMultipleChoiceField(
                required=False,
                widget=FilteredSelectMultiple("Food Items", is_stacked=False),
                queryset=self._get_food_items_queryset()
            )
        
        # Populate initial data if editing existing instance
        if hasattr(self, 'instance') and self.instance.pk:
            self._populate_initial_data()

    def _get_food_items_queryset(self):
        """Override in subclasses to filter by food type"""
        return FoodItem.objects.all()
    
    def _populate_initial_data(self):
        """Populate form with existing option data"""
        for option in self.instance.options.all():
            weekday_name = WEEKDAYS.get(option.weekday)
            if weekday_name:
                self.initial[weekday_name] = option.food_items.all()

    class Meta:
        widgets = {
            'week': DateInput(),
        }
        exclude = ('created_at', 'options')

    def save(self, commit=True):
        """Save form and create/update options for each weekday"""
        form_instance = super().save(commit)
        
        for weekday_num, weekday_name in WEEKDAYS.items():
            selected_items = self.cleaned_data.get(weekday_name, [])
            
            # Get or create option for this weekday
            option, created = Option.objects.get_or_create(
                weekday=weekday_num,
                defaults={'weekday': weekday_num}
            )
            
            # Update food items for this option
            option.food_items.set(selected_items)
            option.save()
            
            # Add option to form if not already added
            form_instance.options.add(option)
        
        return form_instance


class NewLunchForm(BaseWeeklyForm):
    """Form for creating/editing lunch forms"""
    
    def _get_food_items_queryset(self):
        return FoodItem.objects.filter(type=FoodItem.LUNCH)

    class Meta(BaseWeeklyForm.Meta):
        model = LunchForm


class NewSnacksForm(BaseWeeklyForm):
    """Form for creating/editing snacks forms"""
    
    def _get_food_items_queryset(self):
        return FoodItem.objects.filter(type=FoodItem.SNACKS)

    class Meta(BaseWeeklyForm.Meta):
        model = SnacksForm


# Admin Actions
@admin.action(description="Print orders for selected forms")
def print_orders(modeladmin, request, queryset):
    """Print orders for kitchen preparation"""
    if queryset.count() > 1:
        messages.error(request, "You can only print orders for 1 form at a time.")
        return
    
    form_id = queryset.first().id
    return redirect(f'/admin/print_form/{form_id}')


@admin.action(description="Check quantities for selected forms")
def check_quantities(modeladmin, request, queryset):
    """Check quantities needed for food preparation"""
    if queryset.count() > 1:
        messages.error(request, "You can only check quantities for 1 form at a time.")
        return
    
    form_id = queryset.first().id
    return redirect(f'/admin/check_quantities/{form_id}')


@admin.action(description="Mark orders as paid")
def set_paid(modeladmin, request, queryset):
    """Mark selected orders as paid"""
    count = queryset.update(paid=True)
    messages.success(request, f"{count} orders marked as paid.")


@admin.action(description="Mark orders as unpaid")
def set_unpaid(modeladmin, request, queryset):
    """Mark selected orders as unpaid"""
    count = queryset.update(paid=False)
    messages.success(request, f"{count} orders marked as unpaid.")


@admin.action(description="Check order details")
def check_order(modeladmin, request, queryset):
    """View detailed order information"""
    if queryset.count() > 1:
        messages.error(request, "You can only check 1 order at a time.")
        return
    
    order_id = queryset.first().id
    return redirect(f'/admin/check_order/{order_id}')


# Admin Classes
class LunchFormAdmin(admin.ModelAdmin):
    """Admin interface for lunch forms"""
    form = NewLunchForm
    list_display = ["display_week", "active", "get_total_orders", "id"]
    list_filter = ["active", "created_at"]
    search_fields = ["week"]
    actions = [print_orders, check_quantities]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("week", "active")
        }),
        ("Weekly Menu", {
            "fields": tuple(WEEKDAYS.values()),
            "description": "Select food items available for each day of the week."
        }),
    )


class SnacksFormAdmin(admin.ModelAdmin):
    """Admin interface for snacks forms"""
    form = NewSnacksForm
    list_display = ["display_week", "active", "get_total_orders", "id"]
    list_filter = ["active", "created_at"]
    search_fields = ["week"]
    actions = [print_orders, check_quantities]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("week", "active")
        }),
        ("Weekly Menu", {
            "fields": tuple(WEEKDAYS.values()),
            "description": "Select snack items available for each day of the week."
        }),
    )


class FoodItemAdmin(admin.ModelAdmin):
    """Admin interface for food items"""
    list_display = ["name", "price", "type", "image_displayed"]
    list_filter = ["type"]
    search_fields = ["name"]
    ordering = ["type", "name"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "type", "price")
        }),
        ("Display", {
            "fields": ("image",),
            "description": "URL to the food item image"
        }),
    )


class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for user profiles"""
    list_display = ["name", "user", "role", "department", "coins", "get_total_orders", "get_unpaid_orders"]
    list_filter = ["role", "department"]
    search_fields = ["name", "user__email"]
    ordering = ["name"]
    
    fieldsets = (
        ("User Information", {
            "fields": ("user", "name")
        }),
        ("Work Information", {
            "fields": ("role", "department")
        }),
        ("Rewards", {
            "fields": ("coins",),
            "description": "Reward coins earned by the user"
        }),
    )


class FormNameListFilter(admin.SimpleListFilter):
    """Filter orders by form week"""
    title = "form week"
    parameter_name = "week"

    def lookups(self, request, model_admin):
        """Get all unique form weeks for filtering"""
        forms = set(order.form for order in model_admin.model.objects.all())
        return [(form.week, str(form)) for form in forms]

    def queryset(self, request, queryset):
        """Filter queryset by selected week"""
        if self.value():
            return queryset.filter(form__week=self.value())
        return queryset


class OrderAdmin(admin.ModelAdmin):
    """Admin interface for orders"""
    list_display = [
        "id", "display_user", "display_order_type", 
        "form", "get_reservation_count", "total_paid", "paid", "created_at"
    ]
    list_filter = ["paid", FormNameListFilter, "form__active", "created_at"]
    search_fields = ["profile__name", "profile__user__email"]
    actions = [set_paid, set_unpaid, check_order]
    ordering = ["-created_at"]
    
    fieldsets = (
        ("Order Information", {
            "fields": ("profile", "form", "total_paid", "paid")
        }),
        ("Reservations", {
            "fields": ("reservations",),
            "description": "Daily reservations included in this order"
        }),
    )
    
    filter_horizontal = ["reservations"]


class ReservationAdmin(admin.ModelAdmin):
    """Admin interface for reservations"""
    list_display = ["__str__", "weekday", "paid", "get_total_amount"]
    list_filter = ["weekday", "paid"]
    ordering = ["weekday"]


class SelectionAdmin(admin.ModelAdmin):
    """Admin interface for selections"""
    list_display = ["__str__", "food_item", "quantity", "line_total"]
    list_filter = ["food_item__type", "reservation__weekday"]
    search_fields = ["food_item__name"]


# Register models with custom admin site
form_site.register(LunchForm, LunchFormAdmin)
form_site.register(SnacksForm, SnacksFormAdmin)
form_site.register(FoodItem, FoodItemAdmin)
form_site.register(Profile, ProfileAdmin)
form_site.register(Order, OrderAdmin)
form_site.register(Reservation, ReservationAdmin)
form_site.register(Selection, SelectionAdmin)

# Also register with default admin site for convenience
admin.site.register(LunchForm, LunchFormAdmin)
admin.site.register(SnacksForm, SnacksFormAdmin)
admin.site.register(FoodItem, FoodItemAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Order, OrderAdmin)
