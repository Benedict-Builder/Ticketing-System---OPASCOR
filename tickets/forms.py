from django import forms
from .models import Concern

SUBCATEGORY_MAP = {
    'Desktop Publishing/Application Support': [
        'Graphics Layout/Photo Editing',
        'MS Word / Excel / Powerpoint / Visio Formatting',
    ],
    'Coaching Supprot/Set-up Assistance/ Trainings': [
        'IT Devices / Hardware',
        'Software Applications',
        'Equipment / Devices',
        'Technical Services',
    ],
    'Internal & Web-based System Concerns': [
        'Data Correction / Amendments',
        'Opascor Terminal Operating System (OpTOS)',
        'OpTOS Blockcontrol',
        'OpTOS Reefer',
        'OpTOS Analytics',
        'OpTOS Weighing',
    ],
    'Website Access Request': [
        'Internet Access Schedule',
    ],
    'Others (Pls. Specify)': [
        'Others - Please Specify',
    ],
}

class RegisterForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    username = forms.CharField(max_length=50)
    email = forms.EmailField() 
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def clean_username(self):
        from django.contrib.auth.models import User
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken.")
        return username

class ConcernForm(forms.ModelForm):
    class Meta:
        model = Concern
        fields = ['category', 'sub_category', 'description', 'others_specify', 'attachment']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'others_specify': forms.TextInput(attrs={'placeholder': 'Please specify if Others is selected'}),
        }