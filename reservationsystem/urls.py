from django.contrib import admin
from django.urls import path, include
from forms.admin import form_site
from forms.views import print_form

urlpatterns = [
    path("", include("forms.urls")),
    path('admin/print_form/<int:id>/', print_form, name="print_form"),
    path('admin/', form_site.urls),
]
