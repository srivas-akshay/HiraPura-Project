from django import forms
import re

class PhoneLoginForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'input-field', 'autocomplete': 'off'})
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not re.fullmatch(r'[0-9+\-]{7,15}', phone):
            raise forms.ValidationError("ફોન નંબર માન્ય નથી.")
        return phone

class AttendanceForm(forms.Form):
    number_of_people = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': 'કેટલા લોકો આવશે', 'class': 'input-field'})
    )
