from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, StudentProfile, LecturerProfile, ParentProfile, Department


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control form-control-lg'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control form-control-lg'}))


class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    matric_number = forms.CharField(max_length=20)
    department = forms.ModelChoiceField(queryset=Department.objects.filter(is_active=True))
    level = forms.ChoiceField(choices=StudentProfile.LEVEL_CHOICES)
    admission_year = forms.IntegerField(min_value=2000, max_value=2100)
    state_of_origin = forms.CharField(max_length=100, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.STUDENT
        user.status = CustomUser.Status.PENDING
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                matric_number=self.cleaned_data['matric_number'],
                department=self.cleaned_data['department'],
                level=self.cleaned_data['level'],
                admission_year=self.cleaned_data['admission_year'],
                state_of_origin=self.cleaned_data.get('state_of_origin', ''),
            )
        return user


class LecturerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    staff_id = forms.CharField(max_length=20)
    department = forms.ModelChoiceField(queryset=Department.objects.filter(is_active=True))
    title = forms.CharField(max_length=50, required=False)
    specialization = forms.CharField(max_length=200, required=False)
    qualification = forms.CharField(max_length=200, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.LECTURER
        user.status = CustomUser.Status.PENDING
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            user.save()
            LecturerProfile.objects.create(
                user=user,
                staff_id=self.cleaned_data['staff_id'],
                department=self.cleaned_data['department'],
                title=self.cleaned_data.get('title', ''),
                specialization=self.cleaned_data.get('specialization', ''),
                qualification=self.cleaned_data.get('qualification', ''),
            )
        return user


class ParentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    occupation = forms.CharField(max_length=200, required=False)
    ward_matric = forms.CharField(max_length=20, required=False, label='Ward Matric Number (optional)')

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.PARENT
        user.status = CustomUser.Status.PENDING
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            user.save()
            parent = ParentProfile.objects.create(
                user=user,
                occupation=self.cleaned_data.get('occupation', '')
            )
            ward_matric = self.cleaned_data.get('ward_matric', '')
            if ward_matric:
                try:
                    ward = StudentProfile.objects.get(matric_number=ward_matric)
                    parent.wards.add(ward)
                except StudentProfile.DoesNotExist:
                    pass
        return user


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'address', 'profile_picture']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput, min_length=8, label='New Password')
    new_password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm New Password')

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data


class LinkWardForm(forms.Form):
    matric_number = forms.CharField(max_length=20, label='Student Matric Number')
