from django.db import models
from django.contrib.auth.models import User
import datetime
from datetime import timedelta
from django.utils.html import format_html

class FoodItem(models.Model):
    LUNCH = "LUNCH"
    SNACKS = "SNACKS"
    TYPE_CHOICES = ((LUNCH,"Lunch"),(SNACKS,"Snacks"))

    def image_displayed(self):
         return format_html(
            '<img style="width: 125px; height:125px; object-fit: cover;" src="{}">',
            self.image,
        )

    type = models.CharField(max_length=10, choices=TYPE_CHOICES,default=LUNCH)
    name = models.CharField(max_length=200)
    price = models.IntegerField(default=0)
    image = models.CharField(max_length=200)

    def __str__(self):
      return self.name

class Option(models.Model):
    WEEKDAYS =(
        ("1", "monday"),
        ("2", "tuesday"),
        ("3", "wednesday"),
        ("4", "thursday"),
        ("5", "friday"),
    )
    food_items = models.ManyToManyField(FoodItem)
    weekday = models.CharField(max_length=3, choices=WEEKDAYS)



class Reservation(models.Model):
    WEEKDAYS =(
        ("1", "monday"),
        ("2", "tuesday"),
        ("3", "wednesday"),
        ("4", "thursday"),
        ("5", "friday"),
    )
    weekday = models.CharField(max_length=3, choices=WEEKDAYS)
    paid = models.BooleanField(default=False)

class Selection(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def line_total(self):
        return self.quantity * self.food_item.price

class Form(models.Model):


    created_at = models.DateTimeField(default=datetime.datetime.now())

    active = models.BooleanField(default=False)
    week = models.CharField(max_length=50)
    options=models.ManyToManyField(Option)

    def display_week(self):
        def parse_date(week_data):
            year = int(week_data.split("-")[0])
            week = int(week_data.split("W")[-1])

            start_date = datetime.date.fromisocalendar(year,week,1)
            end_date = start_date + timedelta(days=7)

            parsed_date = start_date.strftime("%b %d, %Y") + " - " + end_date.strftime("%b %d %Y")
            return parsed_date

        return parse_date(self.week)

    display_week.short_description = 'Week'

    def display_type(self):
        children = ['lunchform', 'snacksform']
        for c in children:
            try:
                _ = self.__getattribute__(c) # returns child model
            except:
                pass
            else:
                return self.__getattribute__(c)
        else:
            return 'Not specified'

    def __str__(self):
        return self.display_week()

class LunchForm(Form):
    type = "LUNCH"

    def __str__(self):
        return "Lunch Form"


class SnacksForm(Form):
    type = "SNACKS"

    def __str__(self):
        return "Snacks Form"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length = 50, unique = True)
    role = models.CharField(max_length = 20, blank=True, null=True)
    department = models.CharField(max_length = 20, blank=True, null=True)


class Order(models.Model):
    reservations=models.ManyToManyField(Reservation, related_name="order")
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)
    total_paid = models.IntegerField(default=0)

    def display_user(self):
        return self.profile.name

    display_user.short_description = 'User'

    def display_order_type(self):
        return self.form.display_type()

    display_order_type.short_description = "Type"
    # def reservations_display(self):
    #     format_html('<div>{}</div>', "\n".join([format_html('<div><p>{}</p></div',reservation.weekday)] for reservation in self.reservations)

    def __str__(self):
        return self.form.display_week()


