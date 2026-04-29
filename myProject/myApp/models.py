from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
# from .models import Student 

# INTAKE
INTAKE_CHOICES = [
    ('2017', '2017'),
    ('2018', '2018'),
    ('2019', '2019'),
    ('2020', '2020'),
    ('2021', '2021'),
    ('2022', '2022'),
    ('2023', '2023'),
    ('2024', '2024'),
    ('2025', '2025'),
]

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='admin_profiles/', blank=True, null=True)

    def __str__(self):
        return self.user.username

class Subject(models.Model):
    name = models.CharField(max_length=100)  # e.g. "Bahasa Melayu"
    form_level = models.CharField(max_length=10, choices=[('Form 1', 'Form 1'), ('Form 2', 'Form 2')])

    def __str__(self):
        return f"{self.name} ({self.form_level})"

class Classroom(models.Model):
    FORM_LEVEL_CHOICES = [
        ('Form 1', 'Form 1'),
        ('Form 2', 'Form 2'),
    ]

    name = models.CharField(max_length=50, unique=True)
    form_level = models.CharField(max_length=10, choices=FORM_LEVEL_CHOICES)

    def __str__(self):
        return self.name
    
class Exam(models.Model):
    name = models.CharField(max_length=100)  # e.g., Midterm, Final
    year = models.PositiveIntegerField()
    date = models.DateField() 
    
    def __str__(self):
        return f"{self.name} ({self.year})"

#Teacher form
class Teacher(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    RACE_CHOICES = [
        ('Malay', 'Malay'),
        ('Chinese', 'Chinese'),
        ('Indian', 'Indian'),
        ('Other', 'Other'),
    ]

    SUBJECT_CHOICES = [
        ('Reka Bentuk dan Teknologi', 'Reka Bentuk dan Teknologi'),
        ('Bahasa Melayu', 'Bahasa Melayu'),
        ('Bahasa Inggeris', 'Bahasa Inggeris'),
        ('Science', 'Science'),
        ('Matematik', 'Matematik'),
        ('Pendidikan Jasmani', 'Pendidikan Jasmani'),
        ('Pendidikan Seni Visual', 'Pendidikan Seni Visual'),
        ('Pendidikan Islam', 'Pendidikan Islam'),
        ('Pendidikan Moral', 'Pendidikan Moral'),
        ('Geografi', 'Geografi'),
        ('Sejarah', 'Sejarah'),
        ('Pendidikan Sivik', 'Pendidikan Sivik'),
    ]

    CLASS_CHOICES_FORM_1 = [
        ('None', 'None'),
        ('1 Cempaka', '1 Cempaka'),
        ('1 Delima', '1 Delima'),
        ('1 Emerald', '1 Emerald'),
    ]

    CLASS_CHOICES_FORM_2 = [
        ('2 Cempaka', '2 Cempaka'),
        ('2 Delima', '2 Delima'),
        ('2 Emerald', '2 Emerald'),
    ]

    form_level = models.CharField(
        max_length=10,
        choices=[('Form 1', 'Form 1'), ('Form 2', 'Form 2')],
        blank=True,  # allow empty for legacy records
        null=True
    )
    name = models.CharField(max_length=100)
    race = models.CharField(max_length=10, choices=RACE_CHOICES)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    ic_number = models.CharField(max_length=14, unique=True)
    age = models.IntegerField()
    profile_picture = models.ImageField(upload_to='teacher_profiles/', blank=True, null=True)
    intake = models.CharField(max_length=10, choices=INTAKE_CHOICES)
    number_matric_teach = models.CharField(max_length=20, unique=True)
    
    assigned_class = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True)
    subjects = models.ManyToManyField(Subject)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')

    def __str__(self):
        return self.name
    
# Parent form     
class ParentProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.user.username} ↔ {self.student.full_name}"
    
class ParentLoginHistory(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.parent.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
class AdminLoginHistory(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}" 
    
class TeacherLoginHistory(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.teacher.username} logged in at {self.timestamp}"       
   
# Student form 
class Student(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    RACE_CHOICES = [
        ('Malay', 'Malay'),
        ('Chinese', 'Chinese'),
        ('Indian', 'Indian'),
        ('Other', 'Other'),
    ]
    
    FORM_LEVEL_CHOICES = [
        ('Form 1', 'Form 1'),
        ('Form 2', 'Form 2'),
    ]

    full_name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=50)
    ic_number = models.CharField(max_length=14, unique=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    race = models.CharField(max_length=10, choices=RACE_CHOICES)
    address = models.TextField()

    intake = models.CharField(max_length=10, choices=INTAKE_CHOICES)
    number_matric_std = models.CharField(max_length=20, blank=True, unique=True)
    student_class = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True)

    subjects = models.ManyToManyField(Subject) 

    guardian_name = models.CharField(max_length=100)
    guardian_contact = models.CharField(max_length=20)
    guardian_email = models.EmailField()

    registered_by = models.ForeignKey('myApp.Teacher', null=True, blank=True, on_delete=models.SET_NULL, related_name='registered_students')
    # who registered this student

    def __str__(self):
        return self.full_name

# Subject marking with season
class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    marks = models.FloatField()

    class Meta:
        unique_together = ['student', 'subject', 'exam']
    
# Student Personal Info 
class StudentPersonal(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    
    ADDRESS_CHOICES = [
        ('U', 'Urban'), 
        ('R', 'Rural')
    ]
    
    FAMSIZE_CHOICES = [
        ('B40', 'B40'), 
        ('M40', 'M40'), 
        ('T20', 'T20')
    ]
    
    PSTATUS_CHOICES = [
        ('T', 'Together'), 
        ('A', 'Apart')
    ]
    
    GUARDIAN_CHOICES = [
        ('mother', 'Mother'), 
        ('father', 'Father'), 
        ('other', 'Other')
    ]
    
    MOTHER_JOB_CHOICES = [
        ('teacher', 'Teacher'),
        ('admin', 'Administrative'),
        ('police', 'Police'),
        ('housewife', 'Housewife'),
        ('other', 'Other')
    ]

    FATHER_JOB_CHOICES = [
        ('teacher', 'Teacher'),
        ('admin', 'Administrative'),
        ('police', 'Police'),
        ('househusband', 'Househusband'),
        ('other', 'Other')
    ]
    
    YES_NO = [('yes', 'Yes'), ('no', 'No')]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    # performance_notes = models.TextField(blank=True)
    address = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    famsize = models.CharField(max_length=3, choices=FAMSIZE_CHOICES)
    pstatus = models.CharField(max_length=1, choices=PSTATUS_CHOICES)
    mjob = models.CharField(max_length=20, choices=MOTHER_JOB_CHOICES)
    fjob = models.CharField(max_length=20, choices=FATHER_JOB_CHOICES)
    guardian = models.CharField(max_length=10, choices=GUARDIAN_CHOICES)
    famsup = models.CharField(max_length=3, choices=YES_NO)
    traveltime = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
    )
    # 9. Study Time (1-5)
    studytime = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    # 10. Merit (0-3)
    merit = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(3)],
    )
    # 12. Activities (0-4)
    activities = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
    )
    # 13. Internet (0-4)
    internet = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
    )
    # 14. Family Relationship (1-5)
    famrel = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    # 15. Free time after school (1-5)
    freetime = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    # 16. Hang out (Go out) (1-5)
    goout = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    # 17. Health (1-5)
    health = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    # 3 & 4. Parental Education Level (1-7)
    medu = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)],
    )
    fedu = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)],
    )
    
    class Meta:
        unique_together = ['student', 'exam'] 

    def __str__(self):
        return f"StudentInfo: {self.student.number_matric_std}"
  
# Attendance Student   
class Attendance(models.Model):
    ATTENDANCE_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('R', 'Reason (Excused)'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=ATTENDANCE_CHOICES)
    recorded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('student', 'date')  # Prevent double marking

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.get_status_display()}"
    
# Upload Document Admin 
class uploadDocumentAdmin(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='academic_calendars/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    assigned_teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='calendar_files')

    def __str__(self):
        return self.title

    def is_pdf(self):
        return self.file.name.lower().endswith('.pdf')

    def is_image(self):
        return any(self.file.name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png'])

    def file_size_mb(self):
        return round(self.file.size / 1048576, 1)

    def file_type(self):
        return self.file.name.split('.')[-1].upper()

    def recipient_display(self):
        return self.assigned_teacher.email if self.assigned_teacher else "All Staff"
    
# Upload Teacher file    
class TeacherDocument(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='teacher_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.teacher.username})"

    def is_pdf(self):
        return self.file.name.lower().endswith('.pdf')

    def is_image(self):
        return any(self.file.name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png'])

    def file_type(self):
        return self.file.name.split('.')[-1].upper()

    def file_size_mb(self):
        return round(self.file.size / 1048576, 1)    
    
#############################
#document upload model testing
class Document(models.Model):
    title = models.CharField(max_length=255)  # Title for the uploaded file
    uploaded_file = models.FileField(upload_to='uploads/')  # Stores files in 'uploads/' folder
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Saves upload timestamp

    def __str__(self):
        return self.title

