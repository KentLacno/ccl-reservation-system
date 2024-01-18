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

def logout(request):
    logout(request)
    return redirect('index')

@login_required(login_url='/login')
def index(request):
    if not request.user.profile:
        return redirect('login')
    profile = request.user.profile
    active_form = Form.objects.filter(active=True).first()
    
    if not active_form:
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
        "orders": profile.orders.all(),
        "submitted": profile.orders.filter(form=active_form) != None
    }
    return render(request, "forms/index.html", context)
