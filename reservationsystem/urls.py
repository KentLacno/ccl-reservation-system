from django.contrib import admin
from django.urls import path, include
from forms.admin import form_site
from forms.views import print_form, check_quantities

urlpatterns = [
    path("", include("forms.urls")),
    path('admin/print_form/<int:id>/', print_form, name="print_form"),
    path('admin/check_quantities/<int:id>/', check_quantities, name="check_quantities"),
    path('admin/', form_site.urls),
]
