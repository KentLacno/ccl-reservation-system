from django.contrib import admin
from django.urls import path, include
from forms.admin import form_site

urlpatterns = [
    path("", include("forms.urls")),
    path('admin/', form_site.urls),
]
