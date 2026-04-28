from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Complaint, ComplaintUpdate, UserProfile, ROLE_CHOICES


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name  = forms.CharField(max_length=30, required=False)
    email      = forms.EmailField(required=False)
    role       = forms.ChoiceField(choices=ROLE_CHOICES, initial='customer')

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name  = self.cleaned_data.get('last_name',  '')
        user.email      = self.cleaned_data.get('email',      '')
        if commit:
            user.save()
        return user


class ComplaintForm(forms.ModelForm):
    """Form for customers to raise a complaint.
    
    defect_category and priority are intentionally excluded — these are
    decided by admin after reviewing the customer's report.
    """
    image = forms.ImageField(
        required=True,
        label='Evidence Photo (Required)',
        help_text='Upload a clear photo of the defect or screenshot',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'})
    )

    class Meta:
        model  = Complaint
        fields = ['title', 'product_name', 'order_number', 'description', 'image']
        widgets = {
            'title':        forms.TextInput(attrs={'placeholder': 'Short summary of the defect'}),
            'product_name': forms.TextInput(attrs={'placeholder': 'Name of the product'}),
            'order_number': forms.TextInput(attrs={'placeholder': 'Order/Invoice number (optional)'}),
            'description':  forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe the defect in detail…'}),
        }


class ComplaintUpdateForm(forms.ModelForm):
    class Meta:
        model   = ComplaintUpdate
        fields  = ['message']
        widgets = {'message': forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Add a note, update, or resolution details…',
        })}


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name  = forms.CharField(max_length=30, required=False)
    email      = forms.EmailField(required=False)

    class Meta:
        model  = UserProfile
        fields = ['phone', 'department']
