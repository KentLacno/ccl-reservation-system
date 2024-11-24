from django.urls import path

from . import views

urlpatterns = [
    path("login", views.login, name="login"),
    path("callback", views.callback, name="callback"),
    path("webhooks", views.webhooks, name="webhooks"),
    path("source_callback", views.source_callback, name="source_callback"),
    path("", views.index, name="index"),
    path("delete_order/<int:id>", views.delete_order, name="delete"),
    path("pay_order/<int:id>", views.pay_order, name="pay_order"),

]