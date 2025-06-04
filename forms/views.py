"""
Refactored views with improved readability and structure
"""
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import environ

from .models import LunchForm, SnacksForm, Order, Reservation, Form
from .services import (
    MicrosoftOAuthService, UserService, PaymentService, 
    OrderService, ReportService
)
from .constants import WEEKDAYS

# Environment setup
env = environ.Env()
PAYMONGO_SECRET_KEY = env("PAYMONGO_SECRET_KEY")
HOST_URL = env("HOST_URL")
MICROSOFT_CLIENT_SECRET = env("MICROSOFT_CLIENT_SECRET")
MICROSOFT_CLIENT_ID = env("MICROSOFT_CLIENT_ID")

User = get_user_model()

# Initialize services
oauth_service = MicrosoftOAuthService(
    MICROSOFT_CLIENT_ID, 
    MICROSOFT_CLIENT_SECRET, 
    HOST_URL
)
payment_service = PaymentService(PAYMONGO_SECRET_KEY, HOST_URL)


def login(request):
    """
    Redirect user to Microsoft OAuth authorization
    """
    authorization_url = oauth_service.get_authorization_url()
    context = {"authorization_url": authorization_url}
    return render(request, "forms/login_redirect.html", context)


def callback(request):
    """
    Handle OAuth callback and user authentication
    """
    authorization_code = request.GET.get('code', '')
    if not authorization_code:
        messages.error(request, "Authorization failed. Please try again.")
        return redirect('login')
    
    try:
        # Get user info from Microsoft
        user_data = oauth_service.get_user_info(authorization_code)
        
        # Try to find existing user
        user = User.objects.filter(email=user_data["mail"]).first()
        
        if not user:
            # Create new user if allowed
            user = UserService.create_user_from_oauth(user_data)
            if not user:
                messages.error(request, "Access denied. Invalid email domain.")
                return redirect('login')
        
        # Log user in
        auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect('index')
        
    except Exception as e:
        messages.error(request, "Authentication failed. Please try again.")
        return redirect('login')


@csrf_exempt
def webhooks(request):
    """
    Handle PayMongo payment webhooks
    """
    try:
        webhook_data = json.loads(request.body.decode("utf-8"))
        event_type = webhook_data["data"]["attributes"]["type"]
        
        if event_type == "checkout_session.payment.paid":
            _handle_payment_success(webhook_data["data"]["attributes"])
            
    except (KeyError, json.JSONDecodeError) as e:
        return HttpResponse(status=400)
    
    return HttpResponse(status=200)


def _handle_payment_success(payment_data):
    """
    Handle successful payment webhook
    """
    metadata = payment_data["data"]["attributes"]["metadata"]
    payment_type = metadata["type"]
    item_id = metadata["id"]
    
    if payment_type == "order":
        order = get_object_or_404(Order, id=item_id)
        order.paid = True
        order.save()
    elif payment_type == "reservation":
        reservation = get_object_or_404(Reservation, id=item_id)
        reservation.paid = True
        reservation.save()
        _check_and_update_order_payment_status(reservation)


def _check_and_update_order_payment_status(reservation):
    """
    Check if all reservations in an order are paid and update order status
    """
    order = reservation.order
    all_paid = all(res.paid for res in order.reservations.all())
    if all_paid:
        order.paid = True
        order.save()


@login_required(login_url='/login')
def index(request):
    """
    Main reservation page - display forms and handle submissions
    """
    # Ensure user has profile
    if not hasattr(request.user, "profile"):
        return redirect('login')
    
    profile = request.user.profile
    active_lunch_form = LunchForm.objects.filter(active=True).first()
    active_snacks_form = SnacksForm.objects.filter(active=True).first()
    
    # Handle form submission
    if request.method == "POST":
        return _handle_reservation_submission(request, profile, active_lunch_form, active_snacks_form)
    
    # Prepare context for GET request
    context = _prepare_index_context(profile, active_lunch_form, active_snacks_form)
    
    # Choose template based on device
    template = "forms/mobile_index.html" if request.user_agent.is_mobile else "forms/index.html"
    return render(request, template, context)


def _handle_reservation_submission(request, profile, active_lunch_form, active_snacks_form):
    """
    Handle reservation form submission
    """
    form_type = request.POST.getlist("form")[0]
    
    # Determine which form to use
    if form_type == "lunch_form" and active_lunch_form:
        active_form = active_lunch_form
    elif form_type == "snacks_form" and active_snacks_form:
        active_form = active_snacks_form
    else:
        messages.error(request, "Invalid form submission.")
        return redirect('index')
    
    # Create order from form data
    OrderService.create_order_from_form_data(
        request.POST.dict(), 
        active_form, 
        profile
    )
    
    messages.success(request, "Your reservation has been submitted successfully!")
    return redirect('index')


def _prepare_index_context(profile, active_lunch_form, active_snacks_form):
    """
    Prepare context data for index view
    """
    context = {
        "profile": profile,
        "orders": profile.order_set.all().order_by('-id'),
    }
    
    if active_lunch_form:
        context.update({
            "active_lunch_form": active_lunch_form,
            "lunch_options": active_lunch_form.options.all().order_by("weekday"),
            "submitted_lunch": profile.order_set.filter(form=active_lunch_form).exists()
        })
    
    if active_snacks_form:
        context.update({
            "active_snacks_form": active_snacks_form,
            "snacks_options": active_snacks_form.options.all().order_by("weekday"),
            "submitted_snacks": profile.order_set.filter(form=active_snacks_form).exists()
        })
    
    return context


@csrf_exempt
def delete_order(request, id):
    """
    Delete an unpaid order
    """
    if request.method != "POST":
        return redirect('index')
    
    order = get_object_or_404(Order, id=id)
    
    if not order.paid:
        order.delete()
        messages.success(request, "Order deleted successfully.")
    else:
        messages.error(request, "Cannot delete a paid order.")
    
    return redirect('index')


@csrf_exempt
def pay_order(request, id):
    """
    Create payment session for an order
    """
    if request.method != "POST":
        return redirect('index')
    
    payment_type = request.POST.get("pay_type")
    
    if payment_type == "order":
        return _handle_order_payment(id)
    elif payment_type == "reservation":
        return _handle_reservation_payment(id)
    else:
        return HttpResponse("Invalid payment type", status=400)


def _handle_order_payment(order_id):
    """
    Handle payment for entire order
    """
    order = get_object_or_404(Order, id=order_id)
    
    metadata = {
        "type": "order",
        "id": str(order_id)
    }
    
    checkout_session = payment_service.create_checkout_session(
        order.total_paid, 
        metadata
    )
    
    checkout_url = checkout_session["data"]["attributes"]["checkout_url"]
    return HttpResponse(checkout_url)


def _handle_reservation_payment(reservation_id):
    """
    Handle payment for individual reservation
    """
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Calculate total for this reservation
    total_amount = sum(
        selection.food_item.price * selection.quantity 
        for selection in reservation.selection_set.all()
    )
    
    metadata = {
        "type": "reservation",
        "id": str(reservation_id)
    }
    
    checkout_session = payment_service.create_checkout_session(
        total_amount, 
        metadata
    )
    
    checkout_url = checkout_session["data"]["attributes"]["checkout_url"]
    return HttpResponse(checkout_url)


# Admin views
def print_form(request, id):
    """
    Print form for kitchen preparation (admin only)
    """
    if not request.user.is_superuser:
        return redirect('index')
    
    form = get_object_or_404(Form, id=id)
    orders = Order.objects.filter(form=form)
    display = ReportService.organize_orders_by_weekday(orders)
    
    context = {
        "weekdays": list(WEEKDAYS.values()),
        "form": form,
        "orders": orders,
        "display": display,
    }
    return render(request, "admin/print_form.html", context)


def check_quantities(request, id):
    """
    Check quantities needed for food preparation (admin only)
    """
    if not request.user.is_superuser:
        return redirect('index')
    
    form = get_object_or_404(Form, id=id)
    count = ReportService.generate_quantity_report(form)
    
    context = {"count": count}
    return render(request, "admin/check_quantities.html", context)


def check_order(request, id):
    """
    Check individual order details (admin only)
    """
    if not request.user.is_superuser:
        return redirect('index')
    
    order = get_object_or_404(Order, id=id)
    display = ReportService.organize_orders_by_weekday([order])
    
    context = {
        "weekdays": list(WEEKDAYS.values()),
        "display": display,
    }
    return render(request, "admin/check_order.html", context)


def source_callback(request):
    """
    Placeholder for future payment source callbacks
    """
    return HttpResponse("OK") 