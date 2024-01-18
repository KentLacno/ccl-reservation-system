from django import forms


class ReservationForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
    grade_section = forms.CharField(label="Grade and Section", max_length=100)