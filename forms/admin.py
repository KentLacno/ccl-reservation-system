from django.contrib import admin
from .models import *
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.admin.widgets import AdminDateWidget
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.html import format_html

class DateInput(forms.DateInput):
    input_type = 'week'

class FormAdminArea(admin.AdminSite):
  site_header = "CCL Reservation System Admin"

form_site = FormAdminArea(name="FormAdmin")

class NewLunchForm(forms.ModelForm):
    monday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="LUNCH"))
    tuesday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="LUNCH"))
    wednesday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="LUNCH"))
    thursday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="LUNCH"))
    friday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="LUNCH"))

    def __init__(self, *args, **kwargs):
        super(NewLunchForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs and kwargs["instance"]:
            for option in kwargs["instance"].options.all():
                self.initial[option.get_weekday_display()] = option.food_items.all()

    class Meta:
        model = LunchForm
        exclude=('created_at','options')
        widgets = {
            'week': DateInput(),
        }

    def save(self, commit=True):
        if not self.instance.id:
            form = super(NewLunchForm, self).save()
            weekdays = ["monday","tuesday","wednesday","thursday","friday"]
            for i in range(1,6):
                option = Option.objects.create(weekday=str(i))
                option.food_items.set(FoodItem.objects.filter(id__in=self.data.getlist(weekdays[i-1])))
                option.save()
                form.options.add(option)
        else:
            form = self.instance
            weekdays = ["monday","tuesday","wednesday","thursday","friday"]
            for i in range(1,6):

                if form.options.filter(weekday=str(i)):
                    option = form.options.filter(weekday=str(i)).first()
                else:
                    option = Option.objects.create(weekday=str(i))
                option.food_items.set(FoodItem.objects.filter(id__in=self.data.getlist(weekdays[i-1])))
                option.save()
                form.options.add(option)

        return super(NewLunchForm, self).save(commit=commit)

class NewSnacksForm(forms.ModelForm):
    monday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="SNACKS"))
    tuesday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="SNACKS"))
    wednesday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="SNACKS"))
    thursday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="SNACKS"))
    friday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all().filter(type="SNACKS"))

    def __init__(self, *args, **kwargs):
        super(NewSnacksForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs and kwargs["instance"]:
            for option in kwargs["instance"].options.all():
                self.initial[option.get_weekday_display()] = option.food_items.all()

    class Meta:
        model = SnacksForm
        exclude=('created_at','options')
        widgets = {
            'week': DateInput(),
        }

    def save(self, commit=True):
        if not self.instance.id:
            form = super(NewSnacksForm, self).save()
            weekdays = ["monday","tuesday","wednesday","thursday","friday"]
            for i in range(1,6):
                option = Option.objects.create(weekday=str(i))
                option.food_items.set(FoodItem.objects.filter(id__in=self.data.getlist(weekdays[i-1])))
                option.save()
                form.options.add(option)
        else:
            form = self.instance
            weekdays = ["monday","tuesday","wednesday","thursday","friday"]
            for i in range(1,6):

                if form.options.filter(weekday=str(i)):
                    option = form.options.filter(weekday=str(i)).first()
                else:
                    option = Option.objects.create(weekday=str(i))
                option.food_items.set(FoodItem.objects.filter(id__in=self.data.getlist(weekdays[i-1])))
                option.save()
                form.options.add(option)

        return super(NewSnacksForm, self).save(commit=commit)

@admin.action(description="Print orders for form")
def print_orders(modeladmin, request, queryset):
    if queryset.count() > 1:
        messages.error(request, "You can only print 1 form at a time.")
        return

    return redirect('/admin/print_form/' + str(queryset.first().id))

@admin.action(description="Print/check quantities")
def check_quantites(modeladmin, request, queryset):
    if queryset.count() > 1:
        messages.error(request, "You can only check 1 form at a time.")
        return

    return redirect('/admin/check_quantities/' + str(queryset.first().id))

class LunchFormAdmin(admin.ModelAdmin):
    form = NewLunchForm
    list_display = ["display_week", "active", "id"]
    actions=[print_orders, check_quantites]

form_site.register(LunchForm, LunchFormAdmin, )

class SnacksFormAdmin(admin.ModelAdmin):
    form = NewSnacksForm
    list_display = ["display_week", "active", "id"]
    actions=[print_orders, check_quantites]

form_site.register(SnacksForm, SnacksFormAdmin, )

class FoodItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FoodItemForm, self).__init__(*args, **kwargs)


    class Meta:
        model = FoodItem
        exclude=('weekday', )


class FoodItemFormAdmin(admin.ModelAdmin):
    form = FoodItemForm
    search_fields = ("name",)

    list_display = ["name", "price", "type", "image_displayed"]


form_site.register(FoodItem, FoodItemFormAdmin)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "role", "department",]
    search_fields = ("name",)

form_site.register(Profile, ProfileAdmin)

@admin.action(description="Set paid")
def set_paid(modeladmin, request, queryset):
    queryset.update(paid=True)

@admin.action(description="Set unpaid")
def set_unpaid(modeladmin, request, queryset):
    queryset.update(paid=False)

@admin.action(description="Check order")
def check_order(modeladmin, request, queryset):
    if queryset.count() > 1:
        messages.error(request, "You can only check 1 order at a time.")
        return

    return redirect('/admin/check_order/' + str(queryset.first().id))

class OrderForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Order
        fields = ("paid",)


class FormNameListFilter(admin.SimpleListFilter):
    title = ("form week")
    parameter_name = "week"

    def lookups(self, request, model_admin):

        forms = set([c.form for c in model_admin.model.objects.all()])
        return [(f.week, f.__str__) for f in forms]

    def queryset(self, request, queryset):

        if self.value():
            return queryset.filter(form__week=self.value())



class OrderFormAdmin(admin.ModelAdmin):

    form = OrderForm
    list_display = ["id", "display_user", "display_order_type", "form", "total_paid", "paid",]
    actions=[set_paid, set_unpaid,check_order]
    list_filter = ("paid",FormNameListFilter,)
    search_fields = ("profile__name",)



form_site.register(Order, OrderFormAdmin)



form_site.register(User)
