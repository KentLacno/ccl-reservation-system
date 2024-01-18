from django.contrib import admin
from .models import *
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.admin.widgets import AdminDateWidget


class DateInput(forms.DateInput):
    input_type = 'week'

class FormAdminArea(admin.AdminSite):
  site_header = "CCL Reservation System Admin"

form_site = FormAdminArea(name="FormAdmin")

class NewForm(forms.ModelForm):
    # week = WeekField(widget= AdminDateWidget)
    monday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all())
    tuesday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all())
    wednesday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all())
    thursday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all())
    friday = forms.ModelMultipleChoiceField(required=False, widget=FilteredSelectMultiple("Food Items", is_stacked=False), queryset=FoodItem.objects.all())

    def __init__(self, *args, **kwargs):
        super(NewForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs and kwargs["instance"]:
            for option in kwargs["instance"].options.all():
                self.initial[option.get_weekday_display()] = option.food_items.all()
    
    def somefunction(k, values):
        return dict((k, v) for v in values)
    
    class Meta:
        model = Form
        exclude=('created_at','options')
        widgets = {
            'week': DateInput(),
        }

    def save(self, commit=True):
        if not self.instance.id:
            form = super(NewForm, self).save()
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

        return super(NewForm, self).save(commit=commit)


class FormAdmin(admin.ModelAdmin):
  form = NewForm
  list_display = ["display_week", "active", "id"]

form_site.register(Form, FormAdmin)

class FoodItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FoodItemForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FoodItem
        exclude=('weekday', )


class FoodItemFormAdmin(admin.ModelAdmin):
    form = FoodItemForm
    list_display = ["name", "price", "image"]


form_site.register(FoodItem, FoodItemFormAdmin)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "role", "department",]


form_site.register(Profile, ProfileAdmin)

@admin.action(description="Set paid")
def set_paid(modeladmin, request, queryset):
    print('ay')
    queryset.update(status="p")


@admin.action(description="Print orders")
def print_orders(modeladmin, request, queryset):
    print('ay')
    queryset.update(status="p")

class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Order
        fields = ("paid", )

class OrderFormAdmin(admin.ModelAdmin):
    form = OrderForm
    list_display = ["id", "display_user", "form", "total_paid", "paid"]
    actions=[print_orders]

form_site.register(Order, OrderFormAdmin)

