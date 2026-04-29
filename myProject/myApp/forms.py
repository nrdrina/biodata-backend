from django import forms
from django.contrib.auth.models import User
from .models import Teacher, Student, StudentPersonal, Mark, Classroom, Subject, AdminProfile, Document, uploadDocumentAdmin
from django.core.exceptions import ValidationError

#form teacher registration
class TeacherRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False, label="Confirm Password")

    class Meta:
        model = Teacher
        fields = [
            'form_level',  # ✅ Now you can include it here
            'name', 'race', 'email', 'phone_number', 'address', 'gender',
            'ic_number', 'age', 'profile_picture',
            'intake', 'assigned_class', 'username', 'password'
        ]
        exclude = ['number_matric_teach']
        widgets = {
            'form_level': forms.Select(attrs={'class': 'form-select', 'id': 'form-level-select'}),
            'assigned_class': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_class'].required = False

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password or confirm:
            if password != confirm:
                raise ValidationError("Passwords do not match.")
        return cleaned_data


#form parent registration
class ParentRegistrationForm(forms.Form):
    # student = forms.CharField(label="Child (Student)")
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    email    = forms.EmailField()
    
    class Meta:
        unique_together = ['user', 'student']

    def clean_username(self):
        u = self.cleaned_data["username"]
        if User.objects.filter(username=u).exists():
            raise forms.ValidationError("Username already taken.")
        return u
  
class StudentRegistrationForm(forms.ModelForm):
    # Mark field as NOT required (so form.is_valid() passes)
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,  # ← must be False
        label="Subjects Taken"
    )

    class Meta:
        model = Student
        exclude = ['number_matric_std', 'registered_by', 'student_class']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional filtering by form_level, if needed in future

  
# form student personal 
class StudentPersonalForm(forms.ModelForm):
    class Meta:
        model = StudentPersonal
        exclude = ['student', 'exam'] 
        widgets = {
            # 'exam': forms.Select(attrs={'class': 'form-select'}),
            'medu': forms.NumberInput(attrs={'min': 1, 'max': 6}),
            'fedu': forms.NumberInput(attrs={'min': 1, 'max': 6}),
            'traveltime': forms.NumberInput(attrs={'min': 1, 'max': 4}),
            'studytime': forms.NumberInput(attrs={'min': 1, 'max': 4}),
            'merit': forms.NumberInput(attrs={'min': 0}),
            'famrel': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'freetime': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'goout': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'health': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }    
        
        
# Key in subject mark 
class SubjectMarkForm(forms.ModelForm):
    class Meta:
        model = Mark
        fields = ['student', 'subject', 'exam', 'marks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# EDIT PROFILE ADMIN
class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ['full_name', 'phone', 'profile_picture']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class uploadDocumentAdminForm(forms.ModelForm):
    class Meta:
        model = uploadDocumentAdmin
        fields = ['title', 'file']
        
# TESTING #
#upload focument
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'uploaded_file']