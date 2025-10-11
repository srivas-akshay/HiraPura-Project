from django import forms
import re
from .models import PreEventFeedback, PostEventFeedback

class PhoneLoginForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'input-field', 'autocomplete': 'off','placeholder':"Enter the registered phone no."})
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



class PreEventFeedbackForm(forms.ModelForm):
    class Meta:
        model = PreEventFeedback
        fields = [
            "event",
            "expected_experience_rating",
            "ease_of_registration",
            "clarity_of_communications",
            "expectations",
            "concerns",
        ]
        widgets = {
            "event": forms.Select(attrs={
                "class": "w-full px-4 py-3 rounded-lg bg-black text-white border-gray-600 focus:ring-2 focus:ring-green-400"
            }),
            "expected_experience_rating": forms.HiddenInput(),
            "ease_of_registration": forms.HiddenInput(),
            "clarity_of_communications": forms.HiddenInput(),
            "expectations": forms.Textarea(attrs={
                "class": "hidden mt-3 w-full p-4 border border-gray-600 rounded-xl bg-black text-white text-sm resize-none focus:ring-2 focus:ring-green-400 transition-all duration-300"
            }),
            "concerns": forms.Textarea(attrs={
                "class": "hidden mt-3 w-full p-4 border border-gray-600 rounded-xl bg-black text-white text-sm resize-none focus:ring-2 focus:ring-green-400 transition-all duration-300"
            }),
        }








        
class PostEventFeedbackForm(forms.ModelForm):
    class Meta:
        model = PostEventFeedback
        fields = [
            "event",
            "overall_rating",
            "organization_rating",
            "venue_rating",
            "food_rating",
            "highlights",
            "improvements",
            "would_recommend",
        ]
        widgets = {
            "event": forms.Select(attrs={
                "class": "w-full px-4 py-3 rounded-lg bg-black text-white border-gray-600 focus:ring-2 focus:ring-green-400"
            }),
            "overall_rating": forms.HiddenInput(),
            "organization_rating": forms.HiddenInput(),
            "venue_rating": forms.HiddenInput(),
            "food_rating": forms.HiddenInput(),
            "highlights": forms.Textarea(attrs={
                "class": "mt-3 w-full p-4 border border-gray-600 rounded-xl bg-black text-white text-sm resize-none focus:ring-2 focus:ring-green-400 transition-all duration-300"
            }),
            "improvements": forms.Textarea(attrs={
                "class": "mt-3 w-full p-4 border border-gray-600 rounded-xl bg-black text-white text-sm resize-none focus:ring-2 focus:ring-green-400 transition-all duration-300"
            }),
            "would_recommend": forms.CheckboxInput(attrs={
                "class": "h-5 w-5 rounded border-gray-600 text-green-400 focus:ring-green-500"
            }),
        }