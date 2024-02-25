import random
import string
import requests

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout 
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .forms import ReservationForm

from requests_oauthlib import OAuth2Session

User = get_user_model()
def initialize_oauth():
    client_id = settings.MICROSOFT_CLIENT_ID
    scope = ["User.Read", "profile", "email", "openid"]
    redirect_uri = 'http://localhost:8000/callback'  

    return OAuth2Session(client_id,scope=scope,redirect_uri=redirect_uri)

def login(request):
    authorization_base_url = 'https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize'

    oauth = initialize_oauth()
    authorization_url, state = oauth.authorization_url(authorization_base_url)

    # return HttpResponse('Please go here and authorize ' + authorization_url )
    context = {"authorization_url": authorization_url }
    return render(request, "forms/login_redirect.html", context)
    
def callback(request):
    client_secret = settings.MICROSOFT_CLIENT_SECRET
    token_url = 'https://login.microsoftonline.com/organizations/oauth2/v2.0/token'
    code = request.GET.get('code','')
    oauth = initialize_oauth()
    token = oauth.fetch_token(token_url, client_secret=client_secret, code=code)

    req = requests.get("https://graph.microsoft.com/v1.0/me?$select=displayName,givenName,jobTitle,mail,department,id", headers={"Authorization": "Bearer " + token["access_token"]})
    response = req.json()

    try:
        user = User.objects.get(email=response["mail"])
    except User.DoesNotExist:
        random_password = "".join(random.choice(string.ascii_letters) for i in range(32))
        user = User(username=response["mail"], email=response["mail"], password=make_password(random_password))
        user.save()
        Profile.objects.create(
            user=user,
            name=response["displayName"],
            role=response["jobTitle"],
            department=response["department"]
        )

    auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return HttpResponseRedirect('/')

def source_callback(request):
    print("test")

@login_required(login_url='/login')
def index(request):
    if not hasattr(request.user,"profile"):
        return redirect('login')
    profile = request.user.profile
    active_form = Form.objects.filter(active=True).first()
    
    if not active_form:
        context = {
            "profile" : profile,
            "orders": profile.orders.all(),
            "submitted": len(profile.orders.filter(form=active_form)) != 0
        }
        return render(request, "forms/index.html", context)
    
    if request.method == "POST":
        total_paid = 0
        order = Order.objects.create(form=active_form)
        weekdays = ["monday","tuesday","wednesday","thursday","friday"]
        for i in range(1,6):
            reservation = Reservation.objects.create(weekday=str(i))
            food_items = FoodItem.objects.filter(id__in=request.POST.getlist(weekdays[i-1]))
            for food in food_items.values():
                total_paid += food["price"]
            reservation.food_items.set(food_items)
            reservation.save()
            order.reservations.add(reservation)
        order.total_paid = total_paid
        order.save()
        profile.orders.add(order)
        profile.save()
        return redirect('index')
    
    options = active_form.options.all().order_by("weekday")

    context = {
        "active_form": active_form,
        "options": options,
        "profile" : profile,
        "orders": reversed(profile.orders.all()),
        "submitted": len(profile.orders.filter(form=active_form)) != 0
    }
    return render(request, "forms/index.html", context)

@csrf_exempt
def delete_order(request,id):
    print('zam')
    if request.method == "POST":
        order = Order.objects.get(id=id) 
        if order.paid is False:
            order.delete()
        return redirect('index')

def print_form(request, id):
    if request.user.is_superuser:
        weekdays = Option.WEEKDAYS
        form = Form.objects.get(id=id)
        orders = Order.objects.filter(form=form,paid=True)

        display = {
            "monday": [],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": []
        }

        count = {
            "monday": {},
            "tuesday": {},
            "wednesday": {},
            "thursday": {},
            "friday": {},
            "total": {}
        }

        for option in form.options.all():
            for food_item in option.food_items.all():
                count[weekdays[int(option.weekday)-1][1]][food_item.name] = 0
                if food_item.name not in count["total"]:
                    count["total"][food_item.name] = 0

        for order in orders:
            reservations = order.reservations.all()
            for reservation in reservations:
                for food_item in reservation.food_items.all():
                    count[weekdays[int(reservation.weekday)-1][1]][food_item.name] += 1
                    count["total"][food_item.name] += 1
                display[weekdays[int(reservation.weekday)-1][1]].append(reservation)
               
        print(count)
        context = {
            "weekdays": ["monday","tuesday","wednesday","thursday","friday"],
            "form": form,
            "orders": orders,
            "display": display,
            "count": count,
        }
        return render(request, "admin/print_form.html", context)
    else:
        return redirect('index')
