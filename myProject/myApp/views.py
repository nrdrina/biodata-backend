import matplotlib.pyplot as plt
# import matplotlib.colors as mcolors
# import matplotlib.cm as cm
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from collections import defaultdict, OrderedDict, Counter
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from dateutil.parser import parse as date_parse
import io, base64
from weasyprint import HTML
import tempfile
import re
import pandas as pd
import joblib
import os
from io import BytesIO
from calendar import month_name
import base64
from datetime import datetime
from django.utils import timezone
from django.utils.timezone import now
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from .forms import DocumentForm, TeacherRegistrationForm, StudentRegistrationForm, StudentPersonalForm, ParentRegistrationForm, AdminProfileForm, uploadDocumentAdminForm
from .models import Document, Teacher, Student, StudentPersonal, Mark, Attendance, Subject, Exam, Classroom, ParentProfile, AdminProfile, ParentLoginHistory, uploadDocumentAdmin, TeacherDocument, AdminLoginHistory, TeacherLoginHistory
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Exists, OuterRef, Count, Q, Avg
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils.http import urlencode
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
import json
import calendar
import random
import string



# EMOJI = ✅📨🎉❌👩⚠

# Check if user is admin
is_admin = lambda u: u.is_superuser

# Check if user is a teacher
is_teacher = lambda u: Teacher.objects.filter(user=u).exists()

is_parent = lambda u: ParentProfile.objects.filter(user=u).exists()

def generate_random_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def is_admin(user):
    return user.is_superuser

# =============== #
# LOGOUT SESSION  # 
# =============== #

# LOGOUT / TEACHER
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def logout_teacher(request):
    logout(request)
    return redirect('loginTeach') 

# LOGOUT / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def logout_admin(request):
    logout(request)
    return redirect('loginAdmin') 

@login_required(login_url='loginParent')
@user_passes_test(is_parent, login_url='loginParent')
def logout_parent(request):
    logout(request)
    return redirect('loginParent') 
# =============== #
#  LOGIN SESSION  # 
# =============== #

# FIRST PAGE LOCALHOST
def homepage_redirect(request):
    return redirect('loginParent')


# LOGIN TEACHER
def loginTeach(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and is_teacher(user):
            login(request, user)
            print("✅ Login successful")
            print("👩 Logged in as:", user.username)
            return redirect('homeTeach')  
        else:
            print("❌ Invalid login or not a teacher")
            return render(request, 'myApp/loginTeach.html', {
                'error': 'Invalid username, password, or not a teacher account.'
            })
    return render(request, 'myApp/loginTeach.html')

# LOGIN ADMIN
def loginAdmin(request):
    profile_image_url = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print("🔎 Username entered:", username)

        try:
            user_obj = User.objects.get(username=username, is_superuser=True)
            print("✅ Found superuser:", user_obj)

            profile = AdminProfile.objects.get(user=user_obj)
            print("👤 Found AdminProfile:", profile)

            if profile.profile_picture:
                print("🖼️ Profile picture exists:", profile.profile_picture.url)
                profile_image_url = profile.profile_picture.url
            else:
                print("❌ No profile picture found.")
        except Exception as e:
            print("🚫 Error fetching profile image:", e)

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            AdminLoginHistory.objects.create(admin=user)
            return redirect('homeAdmin')
        else:
            return render(request, 'myApp/loginAdmin.html', {
                'error': 'Invalid admin login',
                'profile_image_url': profile_image_url
            })

    # 👉 Handle GET: Try to load any existing admin profile for preview
    try:
        latest_admin = AdminProfile.objects.select_related('user').filter(user__is_superuser=True).latest('id')
        if latest_admin.profile_picture:
            profile_image_url = latest_admin.profile_picture.url
    except Exception as e:
        print("⚠️ GET - No preview image available:", e)

    return render(request, 'myApp/loginAdmin.html', {
        "profile_image_url": profile_image_url
    })


# LOGIN TEACHER
def loginParent(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                # Check if the user is linked to a parent profile
                profiles = ParentProfile.objects.filter(user=user)
                if profiles.exists():
                    login(request, user)

                    # ✅ Log login history
                    ParentLoginHistory.objects.create(parent=user)

                    request.session["student_id"] = profiles.first().student.id  
                    return redirect("homeParent")
                else:
                    return render(request, "myApp/loginParent.html", {
                        "error": "This account is not registered as a parent."
                    })
            except Exception as e:
                print("❌ Login error:", e)
                return render(request, "myApp/loginParent.html", {
                    "error": "Something went wrong during login."
                })
        else:
            return render(request, "myApp/loginParent.html", {
                "error": "Invalid username or password."
            })

    return render(request, "myApp/loginParent.html")


# RESET PASS LOGIN PARENT / ADMIN   
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def resetPassParent(request):
    # Show unique parents
    unique_parents = User.objects.filter(parentprofile__isnull=False).distinct()

    if request.method == "POST":
        identifier = request.POST.get("parent_search")  # This is the username
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not new_password or not confirm_password:
            return render(request, "myApp/resetPassParent.html", {
                "unique_parents": unique_parents,
                "error": "Both password fields are required.",
                "title": "Parent Management"
            })

        if new_password != confirm_password:
            return render(request, "myApp/resetPassParent.html", {
                "unique_parents": unique_parents,
                "error": "Passwords do not match.",
                "title": "Parent Management"
            })

        try:
            user = User.objects.get(username=identifier)  # 🔄 safer than email
            user.set_password(new_password)
            user.save()

            send_mail(
            subject="🔐 Your Password Has Been Updated",
            message=f"""
Hi {user.username},

Your parent portal password has been successfully updated by the system administrator.

🆕 New Password: {new_password}

If you did not request this change, please contact the school administration immediately.

Regards,  
Admin System
""",
    from_email="edumind112@gmail.com",
    recipient_list=[user.email],
    fail_silently=True
)

            messages.success(request, f"✅ Password updated and email sent to {user.username}.")
            return redirect('resetPassParent')

        except User.DoesNotExist:
            return render(request, "myApp/resetPassParent.html", {
                "unique_parents": unique_parents,
                "error": "Parent not found.",
                "title": "Parent Management"
            })

    return render(request, "myApp/resetPassParent.html", {
        "unique_parents": unique_parents,
        "title": "Parent Management"
    })
    
    
# RESET PASS LOGIN PARENT / ADMIN   
# RESET TEACHER PASSWORD / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def resetPassTeach(request):
    unique_teachers = User.objects.filter(teacher_profile__isnull=False).distinct()

    if request.method == "POST":
        identifier = request.POST.get("teacher_search")  # this is the username
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not new_password or not confirm_password:
            return render(request, "myApp/resetPassTeach.html", {
                "unique_teachers": unique_teachers,
                "error": "Both password fields are required.",
                "title": "Teacher Password Reset"
            })

        if new_password != confirm_password:
            return render(request, "myApp/resetPassTeach.html", {
                "unique_teachers": unique_teachers,
                "error": "Passwords do not match.",
                "title": "Teacher Password Reset"
            })

        try:
            user = User.objects.get(username=identifier)
            user.set_password(new_password)
            user.save()

            send_mail(
                subject="🔐 Your Teacher Portal Password Has Been Reset",
                message=f"""
Dear {user.username},

Your teacher account password has been updated by the administrator.

🆕 New Password: {new_password}

You can now log in to your portal using the new credentials.

Regards,  
Admin System
""",
                from_email="edumind112@gmail.com",
                recipient_list=[user.email],
                fail_silently=True
            )

            messages.success(request, f"✅ Password updated and email sent to {user.username}.")
            return redirect('resetPassTeach')

        except User.DoesNotExist:
            return render(request, "myApp/resetPassTeach.html", {
                "unique_teachers": unique_teachers,
                "error": "Teacher not found.",
                "title": "Teacher Password Reset"
            })

    return render(request, "myApp/resetPassTeach.html", {
        "unique_teachers": unique_teachers,
        "title": "Teacher Password Reset"
    }) 


# ================ #
#  DELETE SESSION  # 
# ================ #

# DELETE ACCOUNT TEACHER / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == "POST":
        try:
            user = User.objects.get(username=teacher.username)
            user.delete()
        except User.DoesNotExist:
            pass

        teacher.delete()
        messages.success(request, f"✅ Deleted {teacher.name} successfully.")
        return redirect('manageTeach')  
    
    return redirect('manageTeach')


# DELETE DATA STUDENT / TEACHER
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    teacher = student.registered_by

    if request.method == "POST":
        student_name = student.full_name
        intake = student.intake
        class_name = student.student_class.name if student.student_class else "Unassigned"

        # ✅ Notify teacher before deleting
        if teacher and teacher.email:
            message = f"""
Dear {teacher.name},

The following student has been removed from your class:

👤 Student Name: {student_name}
📅 Intake: {intake}
🏫 Class: {class_name}

If you believe this was a mistake, please contact the administrator.

Regards,  
Admin System
""".strip()

            send_mail(
                subject="🚨 Student Removed from Your Class",
                message=message,
                from_email="edumind112@gmail.com",  # replace with your valid admin sender
                recipient_list=[teacher.email],
                fail_silently=True
            )

        student.delete()
        messages.success(request, f"✅ Student '{student_name}' deleted successfully.")
        return redirect('manageStd')

    return render(request, 'myApp/access_denied.html', {
        'message': "Invalid request method."
    })
    

# # DELETE DATA PARENT / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def delete_parent(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "Parent account deleted .")
    return redirect("manageParent")


# ================ #
#   HOME SESSION   # 
# ================ #

# HOME TEACHER
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def homeTeach(request):
    context = {}

    try:
        teacher = request.user.teacher_profile
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect("loginTeach")

    current_year = int(request.GET.get("year", timezone.now().year))
    context["current_year"] = current_year
    context["years"] = list(range(2017, 2026))

    months = list(calendar.month_name)[1:]
    
    attendance_qs = Attendance.objects.filter(
        student__student_class=teacher.assigned_class,
        date__year=current_year
    ).annotate(month=TruncMonth("date"))

    monthly_data = defaultdict(lambda: {"present": 0, "absent": 0, "reason": 0})
    for att in attendance_qs:
        label = att.date.strftime("%B")
        if att.status == "P":
            monthly_data[label]["present"] += 1
        elif att.status == "A":
            monthly_data[label]["absent"] += 1
        elif att.status == "R":
            monthly_data[label]["reason"] += 1

    context["attendance_labels"] = months
    context["attendance_present"] = [monthly_data[m]["present"] for m in months]
    context["attendance_absent"] = [monthly_data[m]["absent"] for m in months]
    context["attendance_reason"] = [monthly_data[m]["reason"] for m in months]

    context["total_students"] = Student.objects.filter(
        student_class=teacher.assigned_class,
        intake=current_year  
    ).count()

    teaching_subjects = teacher.subjects.all()
    teaching_subjects = teacher.subjects.all()
    context["subject_students"] = Mark.objects.filter(
        subject__in=teaching_subjects,
        exam__year=current_year,  
    ).values("student_id").distinct().count()

    exam_qs = Exam.objects.filter(year=current_year).order_by("date")
    model_path = os.path.join(settings.BASE_DIR, 'myApp', 'ml', 'student_risk_model.pkl')
    model, feature_names = joblib.load(model_path)
    
    tab_colors = [
        "#b6e0fe", "#ffd6e0", "#c2f2d0", "#fff2b2", "#ffb8b8", "#f9dcc4",
        "#f7b267", "#a0c4ff", "#b9fbc0", "#f08080"
    ]

    risk_exam_tabs = []

    for idx, exam in enumerate(exam_qs):
        students = Student.objects.filter(student_class=teacher.assigned_class)
        personals = StudentPersonal.objects.filter(student__in=students, exam=exam)
        risk_students = []

        for sp in personals:
            abs_count = Attendance.objects.filter(student=sp.student, date__lt=exam.date, status='A').count()
           
            raw_vector = {
                "health": sp.health,
                "famrel": sp.famrel,
                "studytime": sp.studytime,
                "absence_count": abs_count,
                "activities": getattr(sp, "activities", 0),
                "freetime": getattr(sp, "freetime", 0),
                "internet": getattr(sp, "internet", 0),
                "fedu": getattr(sp, "fedu", 0),
                "medu": getattr(sp, "medu", 0),
                "famsup": 1 if getattr(sp, "famsup", "no") == "yes" else 0,
            }
            input_df = pd.DataFrame([raw_vector])
            input_df = pd.get_dummies(input_df)
            for col in feature_names:
                if col not in input_df.columns:
                    input_df[col] = 0
            input_df = input_df[feature_names]

            prediction = model.predict(input_df)[0]
            if prediction == 1:  
                risk_students.append(sp.student)
        risk_exam_tabs.append({
            "name": exam.name,
            "students": risk_students,
            "color": tab_colors[idx % len(tab_colors)]
        })

    context["risk_exam_tabs"] = risk_exam_tabs
    TeacherLoginHistory.objects.create(teacher=request.user)

    login_qs = TeacherLoginHistory.objects.filter(teacher=request.user).annotate(
        month=TruncMonth("timestamp")
    ).values("month").annotate(count=Count("id")).order_by("month")

    all_months = list(calendar.month_name)[1:]
    login_counts = {entry["month"].strftime("%B"): entry["count"] for entry in login_qs if entry["month"]}
    context["login_labels"] = all_months
    context["login_values"] = [login_counts.get(month, 0) for month in all_months]

    context["title"] = "Home Teacher"

    return render(request, "myApp/homeTeach.html", context)



# HOME ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def homeAdmin(request):
    total_parents = ParentProfile.objects.values("user").distinct().count()
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()

    # Admin login counts per month
    login_qs = AdminLoginHistory.objects.annotate(
        month=TruncMonth("timestamp")
    ).values("month").annotate(count=Count("id")).order_by("month")

    # Prepare list of months from Jan to current
    all_months = list(month_name)[1:]  # month_name[1] = January

    # Convert query result to dict { "Month": count }
    month_counts = {item["month"].strftime("%B"): item["count"] for item in login_qs}

    login_chart = {
        "labels": all_months,
        "values": [month_counts.get(month, 0) for month in all_months]
    }

    # Dropdown filters
    intake_filter = request.GET.get("intake")
    exam_type = request.GET.get("exam_type")

    # All available intakes and exams
    all_intakes = Student.objects.values_list("intake", flat=True).distinct()
    all_exams = Exam.objects.values_list("name", flat=True).distinct()

    # Default pie chart values
    pass_fail_data = {"labels": [], "values": []}
    gender_risk_data = {"labels": [], "values": []}

    if intake_filter and exam_type:
        selected_exam = Exam.objects.filter(name=exam_type, year=int(intake_filter)).first()
        if selected_exam:
            # Pass vs Fail pie chart
            core_subject_ids = [1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,19,22]
            pass_count = 0
            fail_count = 0
            all_students = Student.objects.filter(intake=intake_filter)

            for student in all_students:
                marks = Mark.objects.filter(student=student, exam=selected_exam).select_related("subject")
                core_marks = [m for m in marks if m.subject.id in core_subject_ids]
                total_score = sum(m.marks for m in core_marks)
                subject_count = len(core_marks)
                percent = round((total_score / (subject_count * 100)) * 100, 2) if subject_count else 0
                if percent >= 50:
                    pass_count += 1
                else:
                    fail_count += 1

            pass_fail_data = {
                "labels": ["Pass", "Fail"],
                "values": [pass_count, fail_count]
            }

            # Gender risk breakdown
            male_risk = 0
            female_risk = 0
            personals = StudentPersonal.objects.filter(exam=selected_exam, student__intake=intake_filter)

            for sp in personals:
                student = sp.student
                abs_count = Attendance.objects.filter(
                    student=student,
                    date__lt=selected_exam.date,
                    status='A'
                ).count()
                is_risk = abs_count >= 6 or sp.health <= 2 or sp.famrel <= 2

                if is_risk:
                    if student.gender == 'Male':
                        male_risk += 1
                    elif student.gender == 'Female':
                        female_risk += 1

            gender_risk_data = {
                "labels": ["Male at Risk", "Female at Risk"],
                "values": [male_risk, female_risk]
            }

    return render(request, "myApp/homeAdmin.html", {
        "total_parents": total_parents,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "login_chart_json": json.dumps(login_chart),
        "pass_fail_data_json": json.dumps(pass_fail_data),
        "gender_risk_data_json": json.dumps(gender_risk_data),
        "all_intakes": all_intakes,
        "all_exams": all_exams,
        "intake_filter": intake_filter,
        "exam_type": exam_type,
        "title": "Admin Dashboard"
    })





# HOME PARENT
@login_required(login_url='loginParent')
@user_passes_test(is_parent, login_url='loginParent')
def homeParent(request):
    parent_user = request.user
    linked_profiles = ParentProfile.objects.select_related('student').filter(user=parent_user)

    selected_child_id = request.GET.get("child") or (
        linked_profiles.first().student.id if linked_profiles.exists() else None
    )

    selected_child = None
    attendance_data = {"labels": ["Absent", "Present"], "values": [0, 0]}
    login_data = {"labels": [], "values": []}
    chart_labels = []
    chart_data = []
    bar_colors = []
    color_palette = [
        "#b6e0fe", "#ffd6e0", "#c2f2d0", "#fff2b2", "#ffb8b8",
        "#f9dcc4", "#f7b267", "#a0c4ff", "#b9fbc0", "#f08080"
    ]
    exam_types = []
    exam_type = request.GET.get("exam_type")

    if selected_child_id:
        try:
            selected_child = Student.objects.select_related("student_class").get(id=selected_child_id)

            # Get all exams for this student's intake
            exam_qs = Exam.objects.filter(year=selected_child.intake).order_by('date')
            exam_types = [e.name for e in exam_qs]

            total = selected_child.attendance_set.count()
            absent = selected_child.attendance_set.filter(status='A').count()
            attendance_data["values"] = [absent, total - absent]

            # Pick current or first available
            if not exam_type and exam_types:
                exam_type = exam_types[0]

            # Always fetch marks for the current exam_type
            marks = Mark.objects.filter(
                student=selected_child,
                exam__name=exam_type,
                exam__year=selected_child.intake
            ).select_related("subject")
            all_marks = marks

            core_subject_ids = [1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,19,22]
            fail_important_ids = [1, 6, 12, 17]
            subject_failures = []
            grade_summary = defaultdict(int)

            def get_grade(score):
                if score >= 90: return "A+"
                elif score >= 85: return "A"
                elif score >= 80: return "A-"
                elif score >= 75: return "B+"
                elif score >= 70: return "B"
                elif score >= 60: return "C+"
                elif score >= 50: return "C"
                elif score >= 45: return "D"
                elif score >= 40: return "E"
                else: return "G"

            for mark in all_marks:
                grade = get_grade(mark.marks)
                if mark.subject.id in core_subject_ids:
                    grade_summary[grade] += 1
                if mark.subject.id in fail_important_ids and mark.marks < 40:
                    subject_failures.append(mark.subject.name)

            ordered_grades = ["A+", "A", "A-", "B+", "B", "C+", "C", "D", "E", "G"]
            grade_summary_ordered = {g: grade_summary[g] for g in ordered_grades if grade_summary[g] > 0}

            chart_labels = [m.subject.name for m in marks]
            chart_data = [m.marks for m in marks]
            bar_colors = [color_palette[i % len(color_palette)] for i in range(len(chart_labels))]
            # ------------------------------------

            print("Available Exams:", list(exam_types))
            print("Selected exam_type:", exam_type)
            print("Marks found:", marks.count())
        except Student.DoesNotExist:
            selected_child = None
            chart_labels, chart_data, bar_colors = [], [], []

    # LOGIN CHART
    login_data_qs = ParentLoginHistory.objects.filter(parent=request.user).annotate(
        month=TruncMonth("timestamp")
    ).values("month").annotate(count=Count("id")).order_by("month")

    login_data["labels"] = list(calendar.month_name)[1:]
    monthly_count_dict = defaultdict(int)
    for entry in login_data_qs:
        if entry["month"]:
            month = entry["month"].month
            monthly_count_dict[month] = entry["count"]
    login_data["values"] = [monthly_count_dict[m] for m in range(1, 13)]

    return render(request, "myApp/homeParent.html", {
        "linked_profiles": linked_profiles,
        "selected_child": selected_child,
        "attendance_data_json": json.dumps(attendance_data),
        "subject_failures": subject_failures,
        "grade_summary": grade_summary_ordered,
        "login_chart_json": json.dumps(login_data),
        "chart_labels_json": json.dumps(chart_labels),
        "chart_data_json": json.dumps(chart_data),
        "bar_colors_json": json.dumps(bar_colors),
        "exam_types": exam_types,
        "selected_exam_type": exam_type,
        "title": "Parent Dashboard"
    })
  
  
# ================ #
# NEW DATA SESSION # 
# ================ #
    
# REGISTERATION FOR NEW TEACHERS / ADMIN  
# @login_required(login_url='loginAdmin')
# @user_passes_test(is_admin, login_url='loginAdmin')
def is_subject_taken(subject_id, current_teacher_id=None):
        query = Teacher.objects.filter(subjects__id=subject_id)
        if current_teacher_id:
            query = query.exclude(id=current_teacher_id)
        return query.exists()
    
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def newTeach(request):
    form_levels = ['Form 1', 'Form 2']
    subjects = Subject.objects.all()
    classrooms = Classroom.objects.all()
    
    
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            teacher = form.save(commit=False)
            plain_password = form.cleaned_data['password']
            # teacher.password = make_password(plain_password)

            intake = form.cleaned_data.get('intake')
            if intake:
                existing = Teacher.objects.filter(intake=intake).values_list('number_matric_teach', flat=True)
                existing_numbers = [int(str(num)[-2:]) for num in existing if str(num).isdigit() and len(str(num)) >= 2]
                next_number = max(existing_numbers, default=0) + 1
                teacher.number_matric_teach = f"{intake}01{next_number:02d}"
                
            assigned_class = form.cleaned_data.get("assigned_class")
            if assigned_class:
                existing_class_teacher = Teacher.objects.filter(assigned_class=assigned_class).exclude(id=teacher.id).first()
                if existing_class_teacher:
                    form.add_error('assigned_class', f"❌ Class '{assigned_class}' is already assigned to {existing_class_teacher.name}.")    

            subject_ids = []
            i = 0
            while True:
                subject_id = request.POST.get(f"subject_{i}")
                if not subject_id:
                    break
                existing_teacher = Teacher.objects.filter(subjects__id=subject_id).first()
                if existing_teacher:
                    subject_name = Subject.objects.get(id=subject_id).name
                    form.add_error(None, f"❌ Subject '{subject_name}' is already assigned to {existing_teacher.name}.")
                subject_ids.append(subject_id)
                i += 1

            # Stop here if any form error added
            if form.errors:
                return render(request, 'myApp/newTeach.html', {
                    'form': form,
                    'form_levels': form_levels,
                    'subjects': subjects,
                    'classrooms': classrooms,
                    'error': "Please fix the form errors below."
                })
                
            auth_user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=plain_password,
                email=form.cleaned_data['email']
            )
            teacher.user = auth_user
            teacher.save()
            teacher.subjects.set(subject_ids)

            # Prepare data for email
            subject_names = teacher.subjects.values_list('name', flat=True)
            subject_display = ", ".join(subject_names)
            class_name = teacher.assigned_class.name if teacher.assigned_class else "Unassigned"
            form_level = teacher.assigned_class.form_level if teacher.assigned_class else "Unassigned"

            # Send welcome email
            if teacher.email:
                message = f"""
Dear {teacher.name},

🎉 Welcome! Your teacher account has been successfully created.

📝 Login Details:
Username: {auth_user.username}
Password: {plain_password}

📚 You have been assigned to:
Class: {class_name}
Form Level: {form_level}
Subjects: {subject_display}

Please log in to the system and verify your information.

Regards,  
Admin System
""".strip()

                send_mail(
                    subject="👋 Welcome to the Academic Portal - Teacher Account Created",
                    message=message,
                    from_email="edumind112@gmail.com",
                    recipient_list=[teacher.email],
                    fail_silently=True
                )

            return render(request, 'myApp/newTeach.html', {
                'form': TeacherRegistrationForm(),  # reset form
                'success': True,
                'title': 'Register New Teacher',
                'form_levels': form_levels,
                'subjects': subjects,
                'classrooms': classrooms
            })
    else:
        form = TeacherRegistrationForm()

    return render(request, 'myApp/newTeach.html', {
        'form': form,
        'title': 'Register New Teacher',
        'form_levels': form_levels,
        'subjects': subjects,
        'classrooms': classrooms
    })
  
  
# CREATE NEW ACC PARENT / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def newParents(request):
    students = Student.objects.all()
    students_data = [
        {"id": s.id, "name": s.full_name, "matric": s.number_matric_std}
        for s in students
    ]
    error_msgs = []

    if request.method == "POST":
        form = ParentRegistrationForm(request.POST)
        print("📩 Received POST:", request.POST)
        selected_ids = request.POST.get("selected_students", "")
        id_list = [int(i) for i in selected_ids.split(",") if i.strip().isdigit()]

        # --- 1. Check for student conflicts ---
        already_assigned = []
        for student_id in id_list:
            student = Student.objects.filter(pk=student_id).first()
            if student and ParentProfile.objects.filter(student=student).exists():
                already_assigned.append(f"{student.full_name} (Matric: {student.number_matric_std})")

        if already_assigned:
            error_msgs.append("❌ The following children are already assigned to another parent:")
            error_msgs += already_assigned
            
        if User.objects.filter(email=form.data.get("email")).exists():
            error_msgs.append("❌ This email is already used by another user.")    

        if form.is_valid() and id_list and not error_msgs:
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            print("✅ Form is valid.")

            # ✅ Create User
            user = User.objects.create_user(username=username, password=password, email=email)

            # ✅ Create ParentProfile for each selected student
            for student_id in id_list:
                try:
                    student = Student.objects.get(pk=student_id)
                    ParentProfile.objects.create(user=user, student=student)
                except Student.DoesNotExist:
                    continue  # skip invalid ID

            # ✅ Prepare student summary for email
            child_summary = "\n".join([
                f"👶 {Student.objects.get(pk=student_id).full_name} (Matric ID: {Student.objects.get(pk=student_id).number_matric_std})"
                for student_id in id_list
            ])

            # ✅ Send confirmation email
            send_mail(
                subject="🎉 Parent Account Created",
                message=f"""
Dear Parent,

Your account has been successfully created.

📥 Login details:
Username: {username}
Password: {password}

👨‍👩‍👧‍👦 Children Linked to Your Account:
{child_summary}

You can now log in to view their academic progress.

Regards,  
Admin System
""",
                from_email="edumind112@gmail.com",
                recipient_list=[email],
                fail_silently=True
            )

            return render(request, "myApp/newParents.html", {
                "form": ParentRegistrationForm(),
                "students": students,
                "students_data_json": mark_safe(json.dumps(students_data)),
                "title": "Register Parent Account",
                "success": True
            })
        else:
            print("❌ Form errors:", form.errors)

    else:
        form = ParentRegistrationForm()

    return render(request, "myApp/newParents.html", {
        "form": form,
        "students": students,
        "students_data_json": mark_safe(json.dumps(students_data)),
        "title": "Register Parent Account",
        "error_msgs": error_msgs,   # <---- pass errors to template
    })
          

# REGISTER NEW STUDENT / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def register_student_by_admin(request):
    teachers = Teacher.objects.exclude(assigned_class__isnull=True).select_related('assigned_class')

    # Group subjects by form level
    all_subjects = Subject.objects.all()
    grouped_subjects = defaultdict(list)
    for subject in all_subjects:
        grouped_subjects[subject.form_level].append({"id": subject.id, "name": subject.name})

    teacher_subject_map = {
        f"{t.name} ({t.assigned_class})": {
            "id": t.id,
            "form_level": t.assigned_class.form_level
        }
        for t in teachers
    }

    form = StudentRegistrationForm()
    
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        selected_teacher_id = request.POST.get("teacher_id")
        collected_subjects_raw = request.POST.get("collected_subjects", "")
        subject_ids = [s for s in collected_subjects_raw.split(",") if s.strip()]

        # Validate that a teacher and subjects were selected
        if not selected_teacher_id:
            form.add_error("teacher", "Please select a teacher.")
        if not subject_ids:
            form.add_error("subjects", "Please select at least one subject.")

        if form.is_valid() and selected_teacher_id and subject_ids:
            teacher = get_object_or_404(Teacher, id=selected_teacher_id)
            assigned_class = teacher.assigned_class

            # Check current student count for this class
            intake = form.cleaned_data.get('intake')        
            current_count = Student.objects.filter(student_class=assigned_class, intake=intake).count()
            if current_count >= 37:
                form.add_error(None, f"❌ Class '{assigned_class.name}' already has 37 students.")
            else:
                # Proceed with saving student
                student = form.save(commit=False)
                student.registered_by = teacher
                student.student_class = assigned_class

                # Generate matric number
                intake = form.cleaned_data.get('intake')
                if intake:
                    existing = Student.objects.filter(intake=intake).values_list('number_matric_std', flat=True)
                    suffixes = [int(s[-2:]) for s in existing if s.startswith(f"{intake}02") and s[-2:].isdigit()]
                    next_suffix = max(suffixes, default=0) + 1
                    student.number_matric_std = f"{intake}02{next_suffix:02d}"

                student.save()
                student.subjects.set(subject_ids)

                # Send email to teacher
                if teacher.email:
                    message = f"""
    Dear {teacher.name},

    A new student has been registered under your class.

    👤 Student Name: {student.full_name}
    🏫 Class: {assigned_class.name}
    📅 Intake: {student.intake}

    Regards,  
    Admin System
    """.strip()

                    send_mail(
                        subject="📚 New Student Assigned to Your Class",
                        message=message,
                        from_email="edumind112@gmail.com",
                        recipient_list=[teacher.email],
                        fail_silently=True
                    )

                # Render with success
                return render(request, "myApp/newStd.html", {
                    "form": StudentRegistrationForm(),
                    "teachers": teachers,
                    "success": True,
                    "title": "Register Student",
                    "grouped_subjects": json.dumps(grouped_subjects),
                    "teacher_subject_map": json.dumps(teacher_subject_map),
                })
        # else:
        #     form = StudentRegistrationForm()
        #     # Fall-through: form not valid or class full
    return render(request, "myApp/newStd.html", {
        "form": form,
        "teachers": teachers,
        "title": "Register Student",
        "grouped_subjects": json.dumps(grouped_subjects),
        "teacher_subject_map": json.dumps(teacher_subject_map),
    })
        
# REQUEST ADD NEW CHILD / PARENT    
@login_required(login_url='loginParent')
@user_passes_test(is_parent, login_url='loginParent')
def request_child_add(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        matric = request.POST.get("matric")
        parent_email = request.user.email
        parent_username = request.user.username  # always present

        message = f"""
📩 New child linking request

👤 Parent Username: {parent_username}
✉️ Parent Email: {parent_email}

🧒 Child Name: {full_name}
🆔 Matric Number: {matric}

Please verify and take appropriate action.
"""

        # Set the display name to the parent's username
        from_display = f'"{parent_username}" <edumind112@gmail.com>'
        email = EmailMessage(
            subject=f"📩 New Child Linking Request - {parent_username}",
            body=message,
            from_email=from_display,
            to=["edumind112@gmail.com"],
            reply_to=[parent_email] if parent_email else None,
        )
        email.send(fail_silently=True)

        return redirect("/homeParent?toast=child_request")
    return redirect("homeParent")
    
    
# ================= #
# VIEW DATA SESSION # 
# ================= #

# VIEW TEACHER INFO / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def view_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    subjects = Subject.objects.all()
    classrooms = Classroom.objects.all()
    form_levels = ['Form 1', 'Form 2']
    
    subject_pairs = [
        {"form_level": s.form_level, "subject_id": s.id}
        for s in teacher.subjects.all()
    ]

    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            updated_teacher = form.save(commit=False)
            old_email = teacher.email

            # 🔒 Check for class conflict
            assigned_class = form.cleaned_data.get("assigned_class")
            if assigned_class:
                existing_class_teacher = Teacher.objects.filter(assigned_class=assigned_class).exclude(id=teacher.id).first()
                if existing_class_teacher:
                    form.add_error('assigned_class', f"❌ Class '{assigned_class}' is already assigned to {existing_class_teacher.name}.")

            # 🔒 Check subject conflicts
            subject_ids = []
            i = 0
            while True:
                subject_id = request.POST.get(f"subject_{i}")
                if not subject_id:
                    break
                if Teacher.objects.filter(subjects__id=subject_id).exclude(id=teacher.id).exists():
                    subject_name = Subject.objects.get(id=subject_id).name
                    form.add_error(None, f"❌ Subject '{subject_name}' is already assigned to another teacher.")
                subject_ids.append(subject_id)
                i += 1

            # 🚫 Stop if any form error
            if form.errors:
                subject_pairs = [
                    {"form_level": s.form_level, "subject_id": s.id}
                    for s in teacher.subjects.all()
                ]
                return render(request, 'myApp/manageTeachView.html', {
                    'form': form,
                    'teacher': teacher,
                    'title': f"Edit Teacher: {teacher.name}",
                    'form_levels': form_levels,
                    'subjects': subjects,
                    'classrooms': classrooms,
                    'subject_pairs': mark_safe(json.dumps(subject_pairs)),
                    'error': "Please resolve the following issues before saving.",
                })

            # ✅ Proceed to update
            updated_teacher.save()

            user = teacher.user
            user.username = form.cleaned_data['username']
            user.email = form.cleaned_data['email']
            if form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()

            updated_teacher.subjects.set(subject_ids)

            # Notify teacher
            if old_email:
                send_mail(
                    subject="🛠️ Teacher Profile Updated",
                    message=f"""
Dear {updated_teacher.name},

Your teacher profile has been updated by the admin.

Please login and check your details.

Regards,
Admin System
""",
                    from_email="edumind112@gmail.com",
                    recipient_list=[old_email],
                    fail_silently=True
                )

            return render(request, 'myApp/manageTeachView.html', {
                'form': form,
                'teacher': teacher,
                'title': f"Edit Teacher: {teacher.name}",
                'form_levels': form_levels,
                'subjects': subjects,
                'classrooms': classrooms,
                'subject_pairs': mark_safe(json.dumps(subject_pairs)),
                'show_success': True
            })
    else:
        form = TeacherRegistrationForm(instance=teacher)

    return render(request, 'myApp/manageTeachView.html', {
        'form': form,
        'teacher': teacher,
        'title': f"Edit Teacher: {teacher.name}",
        'form_levels': form_levels,
        'subjects': subjects,
        'classrooms': classrooms,
        'subject_pairs': mark_safe(json.dumps(subject_pairs)),
    })
    

# LIST CHILD SELECTED / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def manageParentView(request, parent_id):
    parent_user = get_object_or_404(User, pk=parent_id)
    students = Student.objects.all()
    linked_profiles = ParentProfile.objects.filter(user=parent_user).select_related('student')

    if request.method == "POST":
        # Parse the lists from hidden inputs
        added_ids = request.POST.get("added_students", "").split(",")
        removed_ids = request.POST.get("removed_students", "").split(",")

        added_ids = [int(i) for i in added_ids if i.isdigit()]
        removed_ids = [int(i) for i in removed_ids if i.isdigit()]

        added_students = []
        removed_students = []
        error_count = 0

        # --- Handle Removals ---
        for sid in removed_ids:
            try:
                student = Student.objects.get(pk=sid)
                ParentProfile.objects.filter(user=parent_user, student=student).delete()
                removed_students.append(student)
            except Student.DoesNotExist:
                continue

        # --- Handle Additions ---
        for sid in added_ids:
            try:
                student = Student.objects.get(pk=sid)
                # If student is already linked to a different parent, error!
                if ParentProfile.objects.filter(student=student).exclude(user=parent_user).exists():
                    messages.error(request, f"❌ {student.full_name} (Matric: {student.number_matric_std}) is already assigned to another parent.")
                    error_count += 1
                    continue
                if not ParentProfile.objects.filter(user=parent_user, student=student).exists():
                    ParentProfile.objects.create(user=parent_user, student=student)
                    added_students.append(student)
            except Student.DoesNotExist:
                continue

        # Compose and send summary email if any changes
        if parent_user.email and (added_students or removed_students):
            msg_lines = [f"Dear {parent_user.username},", "", "Here is a summary of updates made to your account:"]
            if added_students:
                msg_lines.append("\n🆕 Children Added:")
                for s in added_students:
                    msg_lines.append(f"- {s.full_name} (Matric: {s.number_matric_std})")
            if removed_students:
                msg_lines.append("\n❌ Children Removed:")
                for s in removed_students:
                    msg_lines.append(f"- {s.full_name} (Matric: {s.number_matric_std})")
            msg_lines.append("\nRegards,\nAdmin System")
            send_mail(
                subject="🔄 Your Parent Account Was Updated",
                message="\n".join(msg_lines),
                from_email="edumind112@gmail.com",
                recipient_list=[parent_user.email],
                fail_silently=True
            )

        if error_count == 0:
            messages.success(request, "✅ Changes have been saved!")

        # Always redirect after POST (PRG pattern)
        return redirect(request.path)

    # For GET and after redirect
    linked_profiles = ParentProfile.objects.filter(user=parent_user).select_related('student')
    return render(request, "myApp/manageParentView.html", {
        "parent_user": parent_user,
        "linked_profiles": linked_profiles,
        "students": students,
        "students_data_json": mark_safe(json.dumps([
            {"id": s.id, "name": s.full_name, "matric": s.number_matric_std}
            for s in students
        ])),
        "title": f"Manage {parent_user.username}'s Children"
    })

# MANAGE STUDENT ViEW INFO / ADMIN     
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def view_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    teachers = Teacher.objects.exclude(assigned_class__isnull=True).select_related('assigned_class')

    # Group subjects by form level
    all_subjects = Subject.objects.all()
    grouped_subjects = defaultdict(list)
    for subject in all_subjects:
        grouped_subjects[subject.form_level].append({"id": subject.id, "name": subject.name})

    teacher_subject_map = {
        f"{t.name} ({t.assigned_class})": {
            "id": t.id,
            "form_level": t.assigned_class.form_level
        }
        for t in teachers
    }

    # ✅ Always define it
    selected_subject_ids = list(student.subjects.values_list('id', flat=True))

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, instance=student)
        submitted_subjects = request.POST.get("collected_subjects", "")
        subject_ids = [s for s in submitted_subjects.split(",") if s.strip()]
        selected_teacher_id = request.POST.get("teacher_id")

        print("Selected teacher:", selected_teacher_id)
        print("Collected subjects:", subject_ids)
        print("Form valid:", form.is_valid())
        print("Form errors:", form.errors)

        if form.is_valid() and selected_teacher_id and subject_ids:
            updated_student = form.save(commit=False)
            updated_student.number_matric_std = student.number_matric_std
            updated_student.registered_by = student.registered_by
            teacher = get_object_or_404(Teacher, id=selected_teacher_id)
            updated_student.student_class = teacher.assigned_class
            updated_student.save()
            updated_student.subjects.set(subject_ids)
            
            return render(request, 'myApp/manageStdView.html', {
                'form': StudentRegistrationForm(instance=updated_student),
                'teachers': teachers,
                'form_level': updated_student.student_class.form_level,
                'title': f"Edit Student: {updated_student.full_name}",
                'grouped_subjects': json.dumps(grouped_subjects),
                'teacher_subject_map': json.dumps(teacher_subject_map),
                'student': updated_student,
                'selected_subject_ids': list(updated_student.subjects.values_list('id', flat=True)),
                'success': True,  # ✅ Trigger modal
            })

    else:
        form = StudentRegistrationForm(instance=student)

    return render(request, 'myApp/manageStdView.html', {
        'form': form,
        'teachers': teachers,
        'form_level': student.student_class.form_level,
        'title': f"Edit Student: {student.full_name}",
        'grouped_subjects': json.dumps(grouped_subjects),
        'teacher_subject_map': json.dumps(teacher_subject_map),
        'student': student,
        'selected_subject_ids': selected_subject_ids,
        'success': False,
    })
    
    
# STUDENT RECORD ViEW INFO / TEACHER     
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def view_student_record(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    teachers = Teacher.objects.exclude(assigned_class__isnull=True).select_related('assigned_class')
    
    # Group subjects by form level
    all_subjects = Subject.objects.all()
    grouped_subjects = defaultdict(list)
    for subject in all_subjects:
        grouped_subjects[subject.form_level].append({"id": subject.id, "name": subject.name})

    teacher_subject_map = {
        f"{t.name} ({t.assigned_class})": {
            "id": t.id,
            "form_level": t.assigned_class.form_level
        }
        for t in teachers
    }

    # ✅ Always define it
    selected_subject_ids = list(student.subjects.values_list('id', flat=True))

    if request.method == 'POST' and request.user.is_superuser:
        form = StudentRegistrationForm(request.POST, instance=student)
        submitted_subjects = request.POST.get("collected_subjects", "")
        subject_ids = [s for s in submitted_subjects.split(",") if s.strip()]
        selected_teacher_id = request.POST.get("teacher_id")

        print("Selected teacher:", selected_teacher_id)
        print("Collected subjects:", subject_ids)
        print("Form valid:", form.is_valid())
        print("Form errors:", form.errors)

        if form.is_valid() and selected_teacher_id and subject_ids:
            updated_student = form.save(commit=False)
            updated_student.number_matric_std = student.number_matric_std
            updated_student.registered_by = student.registered_by
            teacher = get_object_or_404(Teacher, id=selected_teacher_id)
            updated_student.student_class = teacher.assigned_class
            updated_student.save()
            updated_student.subjects.set(subject_ids)

            return render(request, 'myApp/stdRecordView.html', {
                'form': StudentRegistrationForm(instance=updated_student),
                'teachers': teachers,
                'form_level': updated_student.student_class.form_level,
                'title': f"Edit Student: {updated_student.full_name}",
                'grouped_subjects': json.dumps(grouped_subjects),
                'teacher_subject_map': json.dumps(teacher_subject_map),
                'student': updated_student,
                'selected_subject_ids': list(updated_student.subjects.values_list('id', flat=True)),
                'readonly': True,
            })

    else:
        form = StudentRegistrationForm(instance=student)

    return render(request, 'myApp/stdRecordView.html', {
        'form': form,
        'teachers': teachers,
        'form_level': student.student_class.form_level,
        'title': f"Edit Student: {student.full_name}",
        'grouped_subjects': json.dumps(grouped_subjects),
        'teacher_subject_map': json.dumps(teacher_subject_map),
        'student': student,
        'selected_subject_ids': selected_subject_ids,
        'readonly': True,
    })
    
    
# STUDENT LIST RANKING VIEW / TEACHER
# @login_required(login_url='loginTeach')
# @user_passes_test(is_teacher, login_url='loginTeach')    
# def view_student_result(request, student_id):
#     student = get_object_or_404(Student, id=student_id)
#     exam_type = request.GET.get("exam_type", "1st Exam")
#     intake = student.intake

#     # Get the correct exam object
#     exam = Exam.objects.filter(name=exam_type, year=int(intake)).first()

#     # Get all marks for this exam
#     all_marks = Mark.objects.filter(student=student, exam=exam).select_related('subject')

#     # GRADE mapping function
#     def get_grade(score):
#         if score >= 90:
#             return "A+", "Cemerlang"
#         elif score >= 85:
#             return "A", "Cemerlang"
#         elif score >= 80:
#             return "A-", "Cemerlang"
#         elif score >= 75:
#             return "B+", "Kepujian"
#         elif score >= 70:
#             return "B", "Kepujian"
#         elif score >= 60:
#             return "C+", "Baik"
#         elif score >= 50:
#             return "C", "Baik"
#         elif score >= 45:
#             return "D", "Lulus"
#         elif score >= 40:
#             return "E", "Lulus"
#         else:
#             return "G", "Gagal"

#     # Annotate each subject mark with grade and description
#     marks_with_grades = []
#     for mark in all_marks:
#         gred, desc = get_grade(mark.marks)
#         marks_with_grades.append({
#             "subject": mark.subject,
#             "marks": mark.marks,
#             "gred": gred,
#             "desc": desc
#         })

#     # Use only core subject IDs for percentage
#     core_subject_ids = [1, 2, 3, 4, 5, 6, 7, 8, 11]
#     core_marks = [m for m in marks_with_grades if m["subject"].id in core_subject_ids]
#     total_score = sum(m["marks"] for m in core_marks)
#     subject_count = len(core_marks)

#     percent = round((total_score / (subject_count * 100)) * 100, 2) if subject_count else 0

#     return render(request, "myApp/stdRankingView.html", {
#         "student": student,
#         "marks": marks_with_grades,  # Includes grade and desc
#         "exam_type": exam_type,
#         "percent": percent,
#     })

@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach') 
def view_student_result(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    exam_type = request.GET.get("exam_type", "1st Exam")
    intake = student.intake
    prediction_result = None
    prediction_reason = None
    risk_score = None
    raw_vector = {}
    multi_exam_graph = OrderedDict()

    exam = Exam.objects.filter(name=exam_type, year=int(intake)).first()
    all_marks = Mark.objects.filter(student=student, exam=exam).select_related('subject')

    def get_grade(score):
        if score >= 90: return "A+", "Cemerlang"
        elif score >= 85: return "A", "Cemerlang"
        elif score >= 80: return "A-", "Cemerlang"
        elif score >= 75: return "B+", "Kepujian"
        elif score >= 70: return "B", "Kepujian"
        elif score >= 60: return "C+", "Baik"
        elif score >= 50: return "C", "Baik"
        elif score >= 45: return "D", "Lulus"
        elif score >= 40: return "E", "Lulus"
        else: return "G", "Gagal"

    marks_with_grades = []
    subject_grades = defaultdict(int)
    subject_failures = []
    
    core_subject_ids = [1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,19,22]
    fail_important_ids = [1, 6, 12, 17]
    
    for mark in all_marks:
        grade, desc = get_grade(mark.marks)  
        marks_with_grades.append({
            "subject": mark.subject,
            "marks": mark.marks,
            "gred": grade,
            "desc": desc,  
        })

        if mark.subject.id in core_subject_ids:
            subject_grades[grade] += 1 

        if mark.subject.id in fail_important_ids and mark.marks < 40:
            subject_failures.append(mark.subject.name)
    
    core_marks = [m for m in marks_with_grades if m["subject"].id in core_subject_ids]
    total_score = sum(m["marks"] for m in core_marks)
    subject_count = len(core_marks)
    percent = round((total_score / (subject_count * 100)) * 100, 2) if subject_count else 0

    personal = StudentPersonal.objects.filter(student=student, exam=exam).first()

    ###### --------- NEW: Multi-exam Trend Analysis --------- ######
    exam_order = ['1st Exam', '1st Midterm', '2nd Exam', '2nd Midterm', 'Final Exam']
    exam_colors = {
        '1st Exam': "#8a21e7",       
        '1st Midterm': "#d43de8",    
        '2nd Exam': "#e83dbd",       
        '2nd Midterm': "#d72b6d",   
        'Final Exam': "#d72b48"      
    }
    trends = []
    previous = None

    for idx, label in enumerate(exam_order):
        exam_obj = Exam.objects.filter(name=label, year=int(student.intake)).first()
        if not exam_obj:
            continue
        sp = StudentPersonal.objects.filter(student=student, exam=exam_obj).first()
        if not sp:
            continue

        # Calculate absence
        if idx == 0:
            abs_count = Attendance.objects.filter(student=student, date__lt=exam_obj.date, status='A').count()
        else:
            prev_exam = Exam.objects.filter(name=exam_order[idx-1], year=int(student.intake)).first()
            abs_count = Attendance.objects.filter(
                student=student,
                date__gt=prev_exam.date,
                date__lt=exam_obj.date,
                status='A'
            ).count() if prev_exam else 0

        # Calculate percent/score for this exam
        markset = Mark.objects.filter(student=student, exam=exam_obj, subject__id__in=core_subject_ids)
        subj_count = markset.count()
        exam_percent = round((sum(m.marks for m in markset) / (subj_count * 100) * 100), 2) if subj_count else 0
        risk = "Risk" if exam_percent <= 49 else "Not Risk"

        # Prepare trend message
        change_msgs = []
        if previous:
            # Track if at least one change is found per factor
            found_change = False

            if sp.famrel > previous.famrel:
                change_msgs.append("Family relationship improved")
                found_change = True
            elif sp.famrel < previous.famrel:
                change_msgs.append("Family relationship declined")
                found_change = True
            else:
                change_msgs.append("Family relationship unchanged")

            if sp.health > previous.health:
                change_msgs.append("Health improved")
                found_change = True
            elif sp.health < previous.health:
                change_msgs.append("Health declined")
                found_change = True
            else:
                change_msgs.append("Health unchanged")

            if sp.studytime > previous.studytime:
                change_msgs.append("Study time increased")
                found_change = True
            elif sp.studytime < previous.studytime:
                change_msgs.append("Study time decreased")
                found_change = True
            else:
                change_msgs.append("Study time unchanged")

            if abs_count < previous.absence_count:
                change_msgs.append("Absences decreased")
                found_change = True
            elif abs_count > previous.absence_count:
                change_msgs.append("Absences increased")
                found_change = True
            else:
                change_msgs.append("Absences unchanged")

            if sp.freetime > previous.freetime:
                change_msgs.append("Free time increased")
                found_change = True
            elif sp.freetime < previous.freetime:
                change_msgs.append("Free time decreased")
                found_change = True
            else:
                change_msgs.append("Free time unchanged")

            # Optionally, if you only want to show "no improvement" when **all** factors unchanged:
            if not found_change:
                change_msgs = ["No improvement detected, risk factors unchanged"]

        else:
            # For the 1st exam, always show factor reasons if any
            factor_msgs = []
            if sp.studytime <= 2:
                factor_msgs.append("Limited study time")
            if getattr(sp, "famsup", None) == 'no' or getattr(sp, "famsup", None) == 0:
                factor_msgs.append("No family support")
            if sp.famrel <= 2:
                factor_msgs.append("Weak family relationship")
            if sp.health <= 2:
                factor_msgs.append("Poor health condition")
            if abs_count >= 6:
                factor_msgs.append("High absences (>6)")
            if factor_msgs:
                change_msgs.extend(factor_msgs)
            else:
                change_msgs.append("No risk factors detected")
        # Save current absence_count for next compare
        sp.absence_count = abs_count

        multi_exam_graph[label] = {
            "famrel": sp.famrel,
            "health": sp.health,
            "freetime": sp.freetime,
            "studytime": sp.studytime,
            "absence": abs_count,
            "color": exam_colors.get(label, "#888888")
        }
        trends.append({
            "exam": label,
            "date": exam_obj.date,
            "score": exam_percent,
            "risk": risk,
            "trend": ', '.join(change_msgs) if change_msgs else "No major change"
        })
        previous = sp
        previous.absence_count = abs_count

    # Analyze overall pattern for summary
    all_risks = [row['risk'] for row in trends]
    if all(r == "Not Risk" for r in all_risks):
        trend_summary = "Consistently not at risk from 1st Exam to Final Exam."
    elif all(r == "Risk" for r in all_risks):
        trend_summary = "Consistently at risk throughout all exams."
    elif all_risks[-1] == "Risk":
        trend_summary = "Ended at risk. Intervention recommended."
    elif all_risks[0] == "Risk" and all_risks[-1] == "Not Risk":
        trend_summary = "Significant improvement from risk to not risk."
    else:
        trend_summary = "Performance fluctuates. See details below."
    ###### --------- END NEW --------- ######

    if subject_count >= 8 and exam and personal:
        try:
            model_path = os.path.join(settings.BASE_DIR, 'myApp', 'ml', 'student_risk_model.pkl')
            model, feature_names = joblib.load(model_path)

            raw_vector = {
                "health": personal.health,
                "famrel": personal.famrel,
                "studytime": personal.studytime,
                "absence_count": Attendance.objects.filter(student=student, date__lt=exam.date, status='A').count(),
                "activities": personal.activities,
                "freetime": personal.freetime,
                "internet": personal.internet,
                "fedu": personal.fedu,
                "medu": personal.medu,
                "famsup": 1 if personal.famsup == "yes" else 0,
            }

            input_df = pd.DataFrame([raw_vector])
            input_df = pd.get_dummies(input_df)
            for col in feature_names:
                if col not in input_df.columns:
                    input_df[col] = 0
            input_df = input_df[feature_names]

            prediction = model.predict(input_df)[0]
            prediction_result = "Risk" if prediction == 1 else "Not Risk"
            risk_score = model.predict_proba(input_df)[0][1] * 100
            # risk_score = model.predict_proba(input_df)[0][1] * 100 if prediction_result == 1 else 0

            changed_factors = set()
            if personal.studytime <= 2:
                changed_factors.add("limited study time")
            if personal.famsup == 'no':
                changed_factors.add("no family support")
            if personal.famrel <= 2:
                changed_factors.add("weak family relationship")
            if personal.health <= 2:
                changed_factors.add("poor health condition")
            if raw_vector['absence_count'] >= 6:
                changed_factors.add("high absences (>6)")
            changed_factors = list(changed_factors)

            if "Final Exam" in exam.name:
                if percent <= 49:
                    prediction_result = "Risk"
                    prediction_reason = f"Student is at risk. Reason: {', '.join(changed_factors) if changed_factors else 'poor performance'}"
                else:
                    prediction_result = "Not Risk"
                    prediction_reason = "Student scored well in Final Exam. No risk detected."
            else:
                if percent <= 49:
                    prediction_result = "Risk"
                    prediction_reason = f"Student at risk. Early attention needed before Final Exam. Reason: {', '.join(changed_factors) if changed_factors else 'low performance'}"
                elif percent >= 50:
                    prediction_result = "Not Risk"
                    prediction_reason = "Student not at risk. Score is strong."

        except Exception as e:
            prediction_result = f"Prediction error: {e}"
            prediction_reason = ""
            multi_exam_graph = {}
    
    return render(request, "myApp/stdRankingView.html",{
        "student": student,
        "marks": marks_with_grades,
        "exam_type": exam_type,
        "percent": percent,
        "prediction_result": prediction_result,
        "prediction_reason": prediction_reason,
        "subject_failures": subject_failures,
        "grade_summary": dict(subject_grades),
        "personal": personal,
        "risk_score": risk_score,
        "raw_vector": raw_vector,
        "multi_exam_graph": multi_exam_graph,
        "subject_count": subject_count,
        "changed_factors": changed_factors if subject_count >= 8 and exam and personal else [],
        "trends": trends,
        "trend_summary": trend_summary,
    })
    
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')    
def grade_distribution_view(request):
    intake = request.GET.get("intake")
    form_level = request.GET.get("form_level")
    class_id = request.GET.get("class_id")
    exam_type = request.GET.get("exam_type")  # 🔥 NEW

    grades = {
        "A+": (90, 100), "A": (85, 89), "A-": (80, 84),
        "B+": (75, 79), "B": (70, 74), "C+": (60, 69),
        "C": (50, 59), "D": (45, 49), "E": (40, 44), "G": (0, 39)
    }
    
    grade_colors = {
        "A+": "#a3e635", "A": "#b6e0fe", "A-": "#f7d6e0", "B+": "#ffe29a",
        "B": "#cdb4db", "C+": "#f9dcc4", "C": "#f7b267", "D": "#a0c4ff",
        "E": "#b9fbc0", "G": "#f08080"
    }

    filters = Q()
    if intake:
        filters &= Q(student__intake=intake)
    if form_level:
        filters &= Q(subject__form_level=form_level)
    if class_id:
        filters &= Q(student__student_class__id=class_id)
    if exam_type:
        filters &= Q(exam__name=exam_type)

    marks = Mark.objects.select_related('subject').filter(filters)
    subjects = Subject.objects.filter(mark__in=marks).distinct()
    exams = Exam.objects.values_list('name', flat=True).distinct()

    data = []
    for subject in subjects:
        subject_marks = marks.filter(subject=subject)
        grade_counts = {}
        for grade, (low, high) in grades.items():
            count = subject_marks.filter(marks__gte=low, marks__lte=high).count()
            grade_counts[grade] = count

        data.append({
            "subject": f"{subject.name} ({subject.form_level})",
            "grades": grade_counts,
            "total": subject_marks.count(),
        })

    return render(request, "myApp/gradePerformance.html", {
        "data": data,
        "intakes": [str(y) for y in range(2017, 2026)],
        "form_levels": ["Form 1", "Form 2"],
        "classes": Classroom.objects.all(),
        "exams": exams,
        "grade_colors": mark_safe(json.dumps(grade_colors)),
        "selected_intake": intake,
        "selected_level": form_level,
        "selected_class": class_id,
        "selected_exam": exam_type,
        "data_json": mark_safe(json.dumps(data)),
    })
    
    
# ================ #
# PROFILE SESSION  # 
# ================ #

# PROFILE TEACHER
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def profileTeach(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    return render(request, "myApp/profileTeach.html", {
        "teacher": teacher,
        "title": "My Profile"
    })
    
# PROFILE ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def profile_admin(request):
    user = request.user  # The currently logged-in admin user
    profile = AdminProfile.objects.get(user=request.user)
    return render(request, "myApp/profileAdmin.html", {
        "user": user,
        "profile": profile,
        "title": "My Profile (Admin)"
    })
    
# EDIT PROFILE ADMIN    
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def edit_profile_admin(request):
    user = request.user
    profile = AdminProfile.objects.get(user=user)

    if request.method == "POST":
        form = AdminProfileForm(request.POST, request.FILES, instance=profile)

        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if form.is_valid():
            form.save()
            # ✅ Update User fields
            user.username = request.POST.get("username")
            user.email = request.POST.get("email")
            user.save()

            # ✅ Update AdminProfile manually
            profile.full_name = request.POST.get("full_name")
            profile.phone = request.POST.get("phone")
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()  # ✅ Save the updated profile

            # ✅ Handle password
            if new_password and confirm_password:
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, "✅ Password updated.")
                else:
                    messages.error(request, "❌ Passwords do not match.")

            # ✅ Email notification
            send_mail(
                subject="🔔 Your Profile Has Been Updated",
                message=f"""
Hi {user.username},

Your admin profile has been successfully updated.

📧 Email: {user.email}
📱 Phone: {profile.phone}
👤 Full Name: {profile.full_name}

If this wasn't you, please contact the system administrator.

Regards,  
Admin System
""",
                from_email="edumind112@gmail.com",
                recipient_list=[user.email],
                fail_silently=True
            )

            return render(request, "myApp/editProfileAdmin.html", {
                "form": AdminProfileForm(instance=profile),  # updated form
                "user": user,
                "profile": profile,
                "title": "Edit Admin Profile",
                "success": True
            })

        else:
            messages.error(request, "❌ Invalid form data.")
    else:
        form = AdminProfileForm(instance=profile)

    return render(request, "myApp/editProfileAdmin.html", {
        "form": form,
        "user": user,
        "profile": profile,
        "title": "Edit Admin Profile",
        "now": now(),
    })

# ================= #
# LIST DATA SESSION # 
# ================= #

# STUDENT LIST INFO / TEACHER  
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def stdRecord(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        students = Student.objects.filter(registered_by=teacher)
    except Teacher.DoesNotExist:
        students = Student.objects.none()

    selected_intake = request.GET.get('intake')
    query = request.GET.get('q')

    if selected_intake:
        students = students.filter(intake=selected_intake)
    if query:
        students = students.filter(
            Q(full_name__icontains=query) | Q(nickname__icontains=query) | Q(number_matric_std__icontains=query)
        )

    paginator = Paginator(students, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    return render(request, 'myApp/stdRecord.html', {
        'students': page_obj,
        'page_obj': page_obj,
        'intake_years': range(2017, 2025),
        'selected_intake': selected_intake,
        'query': query,
        'title': "Student Records"
    })


# STUDENT LIST RANKING / TEACHER
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def student_ranking(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    selected_year = request.GET.get("year")
    query = request.GET.get("q")

    students = Student.objects.filter(registered_by=teacher)

    if selected_year:
        students = students.filter(intake=selected_year)
    if query:
        students = students.filter(full_name__icontains=query)

    paginator = Paginator(students, 10)  # 10 per page
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return render(request, "myApp/stdRanking.html", {
        "students": page_obj,
        "page_obj": page_obj,
        "years": [str(y) for y in range(2017, 2026)],
        "selected_year": selected_year,
        "query": query,
    })


# ======================= #
# MARKING SUBJECT SESSION # 
# ======================= #

# DISPPLAY LIST NAME FOR MARK / TEACHER
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def subject_marking(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    intake = request.GET.get("intake")
    class_name = request.GET.get("student_class")
    student_class = Classroom.objects.filter(name=class_name).first()
    subject_id = request.GET.get("subject")
    exam_type = request.GET.get("exam_type")

    subjects = teacher.subjects.all().order_by('name')
    
    students = []
    exam = None
    subject = None

    if intake and student_class and subject_id and exam_type:
        subject = get_object_or_404(Subject, pk=subject_id)
        exam = get_object_or_404(Exam, name=exam_type, year=int(intake))
        print("🧪 Filter values:")
        print("  Intake:", intake)
        print("  Class:", student_class)
        print("  Subject ID:", subject_id)
        print("  Exam:", exam_type)
        print("  Exam Object:", exam)

        students = Student.objects.filter(
            intake=intake,
            student_class=student_class,
            subjects=subject
        ).annotate(
            has_mark=Exists(
                Mark.objects.filter(
                    student=OuterRef('pk'),
                    subject=subject,
                    exam=exam
                )
            )
        )
    
    mark_map = {}
    if students and subject and exam:
        mark_qs = Mark.objects.filter(
            subject=subject,
            exam=exam,
            student__in=students
        ).values('student_id', 'marks')
        
        mark_map = {entry['student_id']: entry['marks'] for entry in mark_qs}  
          
    return render(request, "myApp/subMark.html", {
        "subjects": subjects,
        "classes": Classroom.objects.values_list('name', flat=True),
        "years": [str(y) for y in range(2017, 2026)],
        "students": students,
        "subject_id": subject_id,
        "exam_id": exam_type,
        "intake": intake,
        "student_class": student_class,
        "subject": subject,
        "mark_map": mark_map,
        "title": "Student Subject Mark List"
    })

    
# SUBJECT ENRTY MARK & PERSONAL / TEACHER
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def enter_mark_and_personal(request, student_id):
    teacher = get_object_or_404(Teacher, user=request.user)
    student = get_object_or_404(Student, pk=student_id)
    can_edit_personal = teacher.assigned_class == student.student_class

    # ✅ Get subject and exam from GET by ID
    subject_id = request.GET.get("subject")
    exam_name = request.GET.get("exam")
    intake = request.GET.get("intake")

    subject = get_object_or_404(Subject, pk=subject_id) if subject_id else None
    exam = get_object_or_404(Exam, name=exam_name, year=int(intake)) if exam_name else None

    # ✅ Load or initialize personal form
    personal_instance = StudentPersonal.objects.filter(student=student, exam=exam).first()

    if can_edit_personal:
        personal_form = StudentPersonalForm(request.POST or None, instance=personal_instance)
    else:
        personal_form = None  # Hidden in template

    # ✅ Load any existing mark entry
    mark_instance = Mark.objects.filter(student=student, subject=subject, exam=exam).first()
    existing_score = mark_instance.marks if mark_instance else None

    success = False

    if request.method == "POST":
        score = request.POST.get("score")

        if can_edit_personal and personal_form and personal_form.is_valid():
            personal = personal_form.save(commit=False)
            personal.student = student
            personal.exam = exam
            personal.save()

        if subject and exam:
            Mark.objects.update_or_create(
                student=student,
                subject=subject,
                exam=exam,
                defaults={"marks": score}
            )
            success = True

    return render(request, "myApp/subEntryMarkAndPersonal.html", {
        "student": student,
        "subject": subject,
        "exam": exam,
        "intake": intake,
        "existing_score": existing_score,
        "personal_form": personal_form,
        "submitted": success,
        "title": "Mark & Personal Entry"
    })

# =================== #
#  ATTENDANCE SESSION # 
# =================== #

# TAKE ATTENDANCE STUDENT / TEACHER   
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def take_attendance(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    date_str = request.GET.get("date")
    success = request.GET.get("success")

    if date_str:
        try:
            selected_date = date_parse(date_str).date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    students = Student.objects.filter(student_class=teacher.assigned_class)

    attendance_options = ["P", "A", "R"]
    status_colors = {
        "P": "success",
        "A": "danger",
        "R": "warning",
    }

    if request.method == "POST":
        for student in students:
            status = request.POST.get(f"status_{student.id}")
            if status:
                Attendance.objects.update_or_create(
                    student=student,
                    date=selected_date,
                    defaults={"status": status, "recorded_by": teacher}
                )
        return redirect(f"{request.path}?date={selected_date}&success=1")

    existing = Attendance.objects.filter(date=selected_date, student__in=students)
    status_map = {a.student_id: a.status for a in existing}

    summary = {"P": 0, "A": 0, "R": 0}
    for a in existing:
        if a.status in summary:
            summary[a.status] += 1

    return render(request, "myApp/attendance.html", {
        "students": students,
        "date": selected_date,
        "status_map": status_map,
        "attendance_options": attendance_options,
        "status_colors": status_colors,
        "title": "Take Attendance",
        "show_success": success == "1",
        "summary": summary
    })

# =============== #
#  MANAGE SESSION # 
# =============== #

# MANAGE TEACHER / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def manageTeach(request):
    form_filter = request.GET.get("form_level")
    query = request.GET.get("q")

    teachers = Teacher.objects.select_related('assigned_class')

    if form_filter:
        teachers = teachers.filter(assigned_class__form_level=form_filter)

    if query:
        teachers = teachers.filter(Q(name__icontains=query) | Q(username__icontains=query))

    total_count = teachers.count()  # ✅ accurate count AFTER filter/search
    paginator = Paginator(teachers, 8)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    show_success_modal = request.session.pop('teacher_updated', False)

    return render(request, 'myApp/manageTeach.html', {
        'teachers': page_obj,
        'page_obj': page_obj,
        'form_filter': form_filter,
        'total_count': total_count,  # ✅ pass total count to template
        'show_success_modal': show_success_modal,
    })


# MANAGE PARENT / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def manageParent(request):
    query = request.GET.get("q", "")

    # Filter parent users by search if needed
    profiles = ParentProfile.objects.select_related('user', 'student')
    if query:
        profiles = profiles.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query)
        )

    # Count for totals
    grand_total = ParentProfile.objects.values('user').distinct().count()
    filtered_total = profiles.values('user').distinct().count()

    # Group parents
    grouped_parents = defaultdict(list)
    for profile in profiles:
        grouped_parents[profile.user].append(profile.student)

    # Convert to regular list of tuples for pagination: [(user, [students])]
    grouped_parents_items = list(grouped_parents.items())

    # Paginate
    paginator = Paginator(grouped_parents_items, 8)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return render(request, "myApp/manageParent.html", {
        "page_obj": page_obj,                       # Paginated parents
        "grouped_parents": dict(page_obj.object_list),  # For current page only
        "title": "Parent Management",
        "query": query,
        "filtered_total": filtered_total,
        "grand_total": grand_total,
    })


# MANAGE STUDENT / ADMIN
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def manageStd(request):
    selected_intake = request.GET.get("intake")
    query = request.GET.get("q")

    grand_total = Student.objects.count()

    students = Student.objects.select_related("student_class", "registered_by").prefetch_related("subjects")

    if selected_intake:
        students = students.filter(intake=selected_intake)

    # Search filter
    if query:
        students = students.filter(Q(full_name__icontains=query))

    filtered_total = students.count()  # After filter/search

    paginator = Paginator(students, 8)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    intake_years = [str(year) for year in range(2017, 2026)]

    return render(request, "myApp/manageStd.html", {
        "students": page_obj,
        "page_obj": page_obj,
        "selected_intake": selected_intake,
        "intake_years": intake_years,
        "filtered_total": filtered_total,
        "grand_total": grand_total,
        "query": query,
    })

# =================== #
#   SUBJECT STATISTIC # 
# =================== #
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def subject_statistics(request):
    intake = request.GET.get("intake")
    form_level = request.GET.get("form_level")

    subjects = Subject.objects.all()
    students = Student.objects.all()

    if intake:
        students = students.filter(intake=intake)
    if form_level:
        students = students.filter(student_class__form_level=form_level)
        subjects = subjects.filter(form_level=form_level)

    total_students = students.count()

    # Now build subject_data
    subject_data = []
    for subject in subjects:
        count = students.filter(subjects=subject).count()
        percent = (count / total_students * 100) if total_students else 0
        subject_data.append({
            "name": f"{subject.name} ({subject.form_level})",
            "count": count,
            "percent": round(percent, 2),
            "not_percent": round(100 - percent, 2),
        })

    # ✅ Now extract data for chart
    subject_labels = [s["name"] for s in subject_data]
    subject_percents = [s["percent"] for s in subject_data]
    subject_counts = [s["count"] for s in subject_data] 

    return render(request, "myApp/subjectAdmin.html", {
        "subject_data": subject_data,
        "title": "Subject Statistics",
        "intakes": [str(y) for y in range(2017, 2026)],
        "selected_intake": intake,
        "selected_level": form_level,
        "form_levels": ["Form 1", "Form 2"],
        "total_students": total_students,
        "subject_labels_json": json.dumps(subject_labels),
        "subject_percents_json": json.dumps(subject_percents),
        "subject_counts_json": json.dumps(subject_counts)
    })

@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def prediction_dashboard(request):
    intake_filter = request.GET.get('intake')
    exam_type = request.GET.get('exam_type')
    class_risk_data = defaultdict(int)
    variable_comparison = defaultdict(int)
    exam_labels = ['1st Exam', '1st Midterm', '2nd Exam', '2nd Midterm', 'Final Exam']

    # Use SEPARATE lists, not a dict
    limited_study_time_counts = []
    no_family_support_counts = []
    weak_family_relationship_counts = []
    poor_health_condition_counts = []

    if intake_filter and exam_type:
        selected_exam = Exam.objects.filter(name=exam_type, year=int(intake_filter)).first()
        if selected_exam:
            # GET ALL CLASSES FOR THIS INTAKE
            all_classes = Student.objects.filter(intake=intake_filter).values_list('student_class__name', flat=True).distinct()
            for class_name in all_classes:
                class_risk_data[class_name] = 0  # Ensure every class shows, even if zero risk
            
            personals = StudentPersonal.objects.filter(exam=selected_exam, student__intake=intake_filter)
            for sp in personals:
                student = sp.student
                abs_count = Attendance.objects.filter(student=student, date__lt=selected_exam.date, status='A').count()
                is_risk = abs_count >= 6 or sp.health <= 2 or sp.famrel <= 2
                if is_risk:
                    class_risk_data[student.student_class.name] += 1

        for label in exam_labels:
            exam_obj = Exam.objects.filter(name=label, year=int(intake_filter)).first()
            if not exam_obj:
                limited_study_time_counts.append(0)
                no_family_support_counts.append(0)
                weak_family_relationship_counts.append(0)
                poor_health_condition_counts.append(0)
                continue
            all_personals = StudentPersonal.objects.filter(exam=exam_obj, student__intake=intake_filter)
            studytime_count = 0
            famsup_count = 0
            famrel_count = 0
            health_count = 0
            for sp in all_personals:
                if sp.studytime is not None and sp.studytime <= 2:
                    studytime_count += 1
                if getattr(sp, "famsup", None) == 'no':
                    famsup_count += 1
                if sp.famrel is not None and sp.famrel <= 2:
                    famrel_count += 1
                if sp.health is not None and sp.health <= 2:
                    health_count += 1
            limited_study_time_counts.append(studytime_count)
            no_family_support_counts.append(famsup_count)
            weak_family_relationship_counts.append(famrel_count)
            poor_health_condition_counts.append(health_count)

    context = {
        "class_labels": list(class_risk_data.keys()),
        "class_values": list(class_risk_data.values()),
        "intake_filter": intake_filter,
        "exam_labels": exam_labels,
        "limited_study_time_counts": limited_study_time_counts,
        "no_family_support_counts": no_family_support_counts,
        "weak_family_relationship_counts": weak_family_relationship_counts,
        "poor_health_condition_counts": poor_health_condition_counts,
        "exam_type": exam_type,
        "class_risk_data": dict(class_risk_data),
        "variable_comparison": dict(variable_comparison),
        "all_intakes": Student.objects.values_list("intake", flat=True).distinct(),
        "all_exams": Exam.objects.values_list("name", flat=True).distinct(),
    }
    return render(request, "myApp/predictionReport.html", context)



# ========== #
# EXPORT PDF # 
# ========== #
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def export_subject_stats_pdf(request):
    intake = request.POST.get("intake")
    form_level = request.POST.get("form_level")

    students = Student.objects.all()
    subjects = Subject.objects.all()

    if intake:
        students = students.filter(intake=intake)
    if form_level:
        students = students.filter(student_class__form_level=form_level)
        subjects = subjects.filter(form_level=form_level)

    total_students = students.count()

    subject_data = []
    for subject in subjects:
        count = students.filter(subjects=subject).count()
        percent = (count / total_students * 100) if total_students else 0
        subject_data.append({
            "name": f"{subject.name} ({subject.form_level})",
            "count": count,
            "percent": round(percent, 2),
        })

    html = render_to_string("myApp/subjectAdminPDF.html", {
        "subject_data": subject_data,
        "intake": intake,
        "form_level": form_level,
        "total_students": total_students
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="subject_stats_{intake}_{form_level}.pdf"'

    pisa.CreatePDF(io.StringIO(html), dest=response)
    return response

@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')
def export_grade_performance_pdf(request):
    intake = request.GET.get("intake")
    form_level = request.GET.get("form_level")
    class_id = request.GET.get("class_id")
    exam_type = request.GET.get("exam_type")

    filters = Q()
    if intake:
        filters &= Q(student__intake=intake)
    if form_level:
        filters &= Q(subject__form_level=form_level)
    if class_id:
        filters &= Q(student__student_class__id=class_id)
    if exam_type:
        filters &= Q(exam__name=exam_type)

    grades = {
        "A+": (90, 100), "A": (85, 89), "A-": (80, 84),
        "B+": (75, 79), "B": (70, 74), "C+": (60, 69),
        "C": (50, 59), "D": (45, 49), "E": (40, 44), "G": (0, 39)
    }
    
    grade_colors = {
        "A+": "#a3e635", "A": "#b6e0fe", "A-": "#f7d6e0", "B+": "#ffe29a",
        "B": "#cdb4db", "C+": "#f9dcc4", "C": "#f7b267", "D": "#a0c4ff",
        "E": "#b9fbc0", "G": "#f08080"
    }

    marks = Mark.objects.select_related('subject').filter(filters)
    subjects = Subject.objects.filter(mark__in=marks).distinct()
    

    data = []
    for subject in subjects:
        subject_marks = marks.filter(subject=subject)
        grade_counts = {}
        for grade, (low, high) in grades.items():
            count = subject_marks.filter(marks__gte=low, marks__lte=high).count()
            grade_counts[grade] = count

        # 🎯 Generate chart for this subject
        labels = list(grade_counts.keys())
        values = list(grade_counts.values())
        colors = [grade_colors.get(g, "#d1d5db") for g in labels]  # fallback to gray

        plt.figure(figsize=(6, 3))
        plt.bar(labels, values, color=colors, edgecolor='black')
        plt.title(f"{subject.name} ({subject.form_level})")
        plt.xlabel("Grades")
        plt.ylabel("No. of Students")
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        buffer.close()
        plt.close()  # important to avoid memory leak

        data.append({
            "subject": f"{subject.name} ({subject.form_level})",
            "grades": grade_counts,
            "total": subject_marks.count(),
            "chart": chart_base64,  # ✅ attach chart
        })
           

    template = get_template("myApp/gradePerformancePDF.html")
    html = template.render({
        "data": data,
        "intake": intake,
        "grade_colors":grade_colors, 
        "form_level": form_level,
        "class_name": Classroom.objects.get(id=class_id).name if class_id else "All",
        "exam_type": exam_type,
        "date": timezone.now().strftime("%d %B %Y"),
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=grade_performance_{timezone.now().date()}.pdf"
    pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=response)
    return response

@login_required(login_url='loginParent')
@user_passes_test(is_parent, login_url='loginParent')
def export_exam_pdf(request):
    parent_user = request.user
    exam_type = request.GET.get("exam_type")

    profile = ParentProfile.objects.filter(user=parent_user).first()
    if not profile:
        return HttpResponse("No student linked to this parent.")

    student = profile.student
    core_subject_ids = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,25,26]

    marks = Mark.objects.filter(student=student, exam__name=exam_type).select_related("subject")

    if not marks.exists():
        return HttpResponse("❌ No result for this exam yet.")

    core_marks = [m for m in marks if m.subject.id in core_subject_ids]
    if not core_marks:
        return HttpResponse("❌ No core subject results found for this exam.")

    total = sum(m.marks for m in core_marks)
    count = len(core_marks)
    percentage = round((total / (count * 100)) * 100, 2) if count else 0

    template = get_template("myApp/exam_result_pdf.html")
    html = template.render({
        "student": student,
        "exam_type": exam_type,
        "marks": core_marks,
        "percent": percentage,
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{student.full_name}_{exam_type}_Result.pdf"'
    pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=response)
    return response

def download_predict_pdf(request, student_id, exam_type):
    student = get_object_or_404(Student, id=student_id)
    context = get_prediction_context(student, exam_type)
    html_string = render_to_string("myApp/predict_pdf_template.html", context)
    pdf_file = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.number_matric_std}_{exam_type}_risk_report.pdf"'
    return response

def get_prediction_context(student, exam_type):
    intake = student.intake
    exam = Exam.objects.filter(name=exam_type, year=int(intake)).first()
    all_marks = Mark.objects.filter(student=student, exam=exam).select_related('subject')

    def get_grade(score):
        if score >= 90: return "A+", "Cemerlang"
        elif score >= 85: return "A", "Cemerlang"
        elif score >= 80: return "A-", "Cemerlang"
        elif score >= 75: return "B+", "Kepujian"
        elif score >= 70: return "B", "Kepujian"
        elif score >= 60: return "C+", "Baik"
        elif score >= 50: return "C", "Baik"
        elif score >= 45: return "D", "Lulus"
        elif score >= 40: return "E", "Lulus"
        else: return "G", "Gagal"

    core_subject_ids = [1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,19,22]
    subject_failures = []
    subject_grades = defaultdict(int)
    fail_important_ids = [1, 6, 12, 17]
    
    for mark in all_marks:
        grade, desc = get_grade(mark.marks)
        # ... already creating marks_with_grades
        if mark.subject.id in core_subject_ids:
            subject_grades[grade] += 1
        if mark.subject.id in fail_important_ids and mark.marks < 40:
            subject_failures.append(mark.subject.name)
    
    marks_with_grades = [{
        "subject": m.subject, "marks": m.marks, "gred": get_grade(m.marks)[0], "desc": get_grade(m.marks)[1]
    } for m in all_marks]
    
    core_marks = [m for m in marks_with_grades if m["subject"].id in core_subject_ids]
    total_score = sum(m["marks"] for m in core_marks)
    subject_count = len(core_marks)
    percent = round((total_score / (subject_count * 100)) * 100, 2) if subject_count else 0

    personal = StudentPersonal.objects.filter(student=student, exam=exam).first()
    model_path = os.path.join(settings.BASE_DIR, 'myApp', 'ml', 'student_risk_model.pkl')
    model, feature_names = joblib.load(model_path)

    raw_vector = {
        "health": personal.health,
        "famrel": personal.famrel,
        "studytime": personal.studytime,
        "absence_count": Attendance.objects.filter(student=student, date__lt=exam.date, status='A').count(),
        "activities": personal.activities,
        "freetime": personal.freetime,
        "internet": personal.internet,
        "fedu": personal.fedu,
        "medu": personal.medu,
        "famsup": 1 if personal.famsup == "yes" else 0,
    }

    input_df = pd.DataFrame([raw_vector])
    input_df = pd.get_dummies(input_df)
    for col in feature_names:
        if col not in input_df.columns:
            input_df[col] = 0
    input_df = input_df[feature_names]

    prediction = model.predict(input_df)[0]
    risk_score = model.predict_proba(input_df)[0][1] * 100
    prediction_result = "Risk" if prediction == 1 else "Not Risk"
    
    intake = student.intake
    exam_order = ['1st Exam', '1st Midterm', '2nd Exam', '2nd Midterm', 'Final Exam']
    exam_colors = {
        '1st Exam': "#8a21e7",
        '1st Midterm': "#d43de8",
        '2nd Exam': "#e83dbd",
        '2nd Midterm': "#d72b6d",
        'Final Exam': "#d72b48"
    }
    # core_subject_ids = [1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,19,22] 
    # fail_important_ids = [1, 6, 12, 17] 
    # (your core subject ids)
    multi_exam_graph = {}
    trends = []
    previous = None

    for idx, label in enumerate(exam_order):
        exam_obj = Exam.objects.filter(name=label, year=int(student.intake)).first()
        if not exam_obj:
            continue
        sp = StudentPersonal.objects.filter(student=student, exam=exam_obj).first()
        if not sp:
            continue

        # Calculate absences for the period
        if idx == 0:
            abs_count = Attendance.objects.filter(
                student=student,
                date__lt=exam_obj.date,
                status='A'
            ).count()
        else:
            prev_exam = Exam.objects.filter(name=exam_order[idx-1], year=int(student.intake)).first()
            abs_count = Attendance.objects.filter(
                student=student,
                date__gt=prev_exam.date if prev_exam else None,
                date__lt=exam_obj.date,
                status='A'
            ).count() if prev_exam else 0

        # For UI/PDF matching: compute percent and risk for this exam
        markset = Mark.objects.filter(student=student, exam=exam_obj, subject__id__in=core_subject_ids)
        subj_count = markset.count()
        exam_percent = round((sum(m.marks for m in markset) / (subj_count * 100) * 100), 2) if subj_count else 0
        risk = "Risk" if exam_percent <= 49 else "Not Risk"

        # --- Trend messages (factor changes) ---
        change_msgs = []
        if previous:
            found_change = False

            if sp.famrel > previous.famrel:
                change_msgs.append("Family relationship improved")
                found_change = True
            elif sp.famrel < previous.famrel:
                change_msgs.append("Family relationship declined")
                found_change = True
            else:
                change_msgs.append("Family relationship unchanged")

            if sp.health > previous.health:
                change_msgs.append("Health improved")
                found_change = True
            elif sp.health < previous.health:
                change_msgs.append("Health declined")
                found_change = True
            else:
                change_msgs.append("Health unchanged")

            if sp.studytime > previous.studytime:
                change_msgs.append("Study time increased")
                found_change = True
            elif sp.studytime < previous.studytime:
                change_msgs.append("Study time decreased")
                found_change = True
            else:
                change_msgs.append("Study time unchanged")

            if abs_count < getattr(previous, "absence_count", 0):
                change_msgs.append("Absences decreased")
                found_change = True
            elif abs_count > getattr(previous, "absence_count", 0):
                change_msgs.append("Absences increased")
                found_change = True
            else:
                change_msgs.append("Absences unchanged")

            if sp.freetime > previous.freetime:
                change_msgs.append("Free time increased")
                found_change = True
            elif sp.freetime < previous.freetime:
                change_msgs.append("Free time decreased")
                found_change = True
            else:
                change_msgs.append("Free time unchanged")

            if not found_change:
                change_msgs = ["No improvement detected, risk factors unchanged"]
        else:
            # First exam - list factors
            factor_msgs = []
            if sp.studytime <= 2:
                factor_msgs.append("Limited study time")
            if getattr(sp, "famsup", None) == 'no' or getattr(sp, "famsup", None) == 0:
                factor_msgs.append("No family support")
            if sp.famrel <= 2:
                factor_msgs.append("Weak family relationship")
            if sp.health <= 2:
                factor_msgs.append("Poor health condition")
            if abs_count >= 6:
                factor_msgs.append("High absences (>6)")
            if factor_msgs:
                change_msgs.extend(factor_msgs)
            else:
                change_msgs.append("No risk factors detected")

        # Save for next round
        sp.absence_count = abs_count
        previous = sp
        
        multi_exam_graph[label] = {
            "famrel": sp.famrel,
            "health": sp.health,
            "freetime": sp.freetime,
            "studytime": sp.studytime,
            "absence": abs_count,
            "color": exam_colors.get(label, "#888888")
        }
        
        trends.append({
            "exam": label,
            "risk": risk,
            "score": exam_percent,
            "trend": ', '.join(change_msgs) if change_msgs else "No major change"
        })
        
    all_risks = [row['risk'] for row in trends]
    if all(r == "Not Risk" for r in all_risks):
        trend_summary = "Consistently not at risk from 1st Exam to Final Exam."
    elif all(r == "Risk" for r in all_risks):
        trend_summary = "Consistently at risk throughout all exams."
    elif all_risks and all_risks[-1] == "Risk":
        trend_summary = "Ended at risk. Intervention recommended."
    elif all_risks and all_risks[0] == "Risk" and all_risks[-1] == "Not Risk":
        trend_summary = "Significant improvement from risk to not risk."
    else:
        trend_summary = "Performance fluctuates. See details below."

    # For the last selected exam: use change_msgs as your pdf_factor_text
    selected_trend = next(
        (t for t in trends if t['exam'].strip().lower() == exam_type.strip().lower()), None
    )
    pdf_factor_text = selected_trend['trend'] if selected_trend else ""
    
    print("pdf_factor_text:", pdf_factor_text)
    print("trends:", trends)
    print("exam_type:", exam_type)
            
    fig, ax = plt.subplots()
    labels = ['Family Relationship', 'Health', 'Free Time', 'Absence', 'Studytime']
    exam_labels = list(multi_exam_graph.keys())

    # Gather bar values
    data_by_feature = {label: [] for label in labels}
    for exam in exam_labels:
        data = multi_exam_graph[exam]
        data_by_feature['Family Relationship'].append(data['famrel'])
        data_by_feature['Health'].append(data['health'])
        data_by_feature['Free Time'].append(data['freetime'])
        data_by_feature['Absence'].append(data['absence'])
        data_by_feature['Studytime'].append(data['studytime'])

    x = range(len(labels))
    bar_width = 0.12

    for idx, exam in enumerate(exam_labels):
        offset = [i + idx * bar_width for i in x]
        values = [data_by_feature[label][idx] for label in labels]
        color = multi_exam_graph[exam]["color"]
        ax.bar(offset, values, width=bar_width, label=exam, color=color)

    ax.set_xticks([r + bar_width * (len(exam_labels) - 1) / 2 for r in x])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 10)
    ax.legend()
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return {
        "student": student,
        "subject_failures": subject_failures,
        "grade_summary": dict(subject_grades), 
        "exam_type": exam_type,
        "trend_summary": trend_summary,
        "percent": percent,
        "prediction_result": prediction_result,
        "pdf_factor_text": pdf_factor_text,   # <--- use this in your PDF template!
        "risk_score": risk_score,
        "multi_exam_graph": multi_exam_graph,
        "graph_image": image_base64,
        "marks_with_grades": marks_with_grades
    }



# ================= #
# ACADEMIC CALENDAR # 
# ================= #
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')  
def uploadDocument(request):
    query = request.GET.get("q")
    if query:
        files = uploadDocumentAdmin.objects.filter(title__icontains=query).order_by('-uploaded_at')
    else:
        files = uploadDocumentAdmin.objects.all().order_by('-uploaded_at')

    # ✅ Always prepare teacher list here (for both GET and POST)
    teachers_qs = Teacher.objects.exclude(assigned_class__isnull=True).select_related('assigned_class', 'user')
    teachers_serialized = [
        {
            "id": t.user.id,
            "name": t.name,
            "email": t.user.email,
            "class": str(t.assigned_class),
        }
        for t in teachers_qs
    ]

    if request.method == "POST":
        form = uploadDocumentAdminForm(request.POST, request.FILES)
        if form.is_valid():
            calendar = form.save(commit=False)

            email = request.POST.get("teacher")
            if email:
                try:
                    match = re.search(r'\(([^)]+)\)', email)
                    actual_email = match.group(1) if match else email
                    calendar.assigned_teacher = User.objects.filter(email=actual_email).first()
                except User.DoesNotExist:
                    calendar.assigned_teacher = None
            else:
                teacher_id = request.POST.get("assigned_teacher")
                if teacher_id:
                    calendar.assigned_teacher = User.objects.get(id=teacher_id)

            calendar.save()
            if calendar.assigned_teacher:
                send_mail(
                    subject='📥 New Document Uploaded',
                    message=f'Hi {calendar.assigned_teacher.get_full_name()},\n\nA new document titled "{calendar.title}" has been shared with you by the admin. You can view it on your dashboard.',
                    from_email='admin@school.com',
                    recipient_list=[calendar.assigned_teacher.email],
                    fail_silently=True, 
                )
            messages.success(request, "✅ File uploaded successfully.")
            return redirect('academic_document_admin')
    else:
        form = uploadDocumentAdminForm()

    return render(request, "myApp/academicDocumentAdmin.html", {
        "documents": files,  # 🔁 changed from "files"
        "form": form,
        "teachers": teachers_qs,
        "title": "Academic Calendar",
        "teachers_json": json.dumps(teachers_serialized)
    })
    
@login_required(login_url='loginAdmin')
@user_passes_test(is_admin, login_url='loginAdmin')    
def delete_academic_files(request):
    if request.method == "POST":
        ids = request.POST.getlist("selected_files")
        uploadDocumentAdmin.objects.filter(id__in=ids).delete()
        messages.success(request, "🗑️ Selected files deleted.")
    return redirect('academic_document_admin')

    
@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')    
def academic_calendar_teacher(request):
    teacher = request.user
    files = uploadDocumentAdmin.objects.filter(
        Q(assigned_teacher__isnull=True) | Q(assigned_teacher=teacher)
    ).order_by('-uploaded_at')
    file_types = [f.file_type() for f in files]
    type_counts = Counter(file_types)
    print([f.file.name for f in files])
    return render(request, "myApp/academicCalendarTeach.html", {
        "files": files,
        "type_counts": json.dumps(type_counts)
    })


@login_required(login_url='loginTeach')
@user_passes_test(is_teacher, login_url='loginTeach')
def teacher_files(request):
    teacher = request.user
    documents = TeacherDocument.objects.filter(teacher=teacher).order_by('-uploaded_at')

    if request.method == 'POST':
        title = request.POST.get('title')
        uploaded_file = request.FILES.get('file')
        if title and uploaded_file:
            TeacherDocument.objects.create(teacher=teacher, title=title, file=uploaded_file)

        return redirect('teacher_files')  # Name of your URL pattern

    return render(request, 'myApp/teacher_files.html', {
        'documents': documents,
        'title': 'My Files',
    })
    
@login_required
@user_passes_test(is_teacher, login_url='loginTeach')
def delete_teacher_file(request):
    if request.method == 'POST':
        selected = request.POST.getlist('selected_files')
        TeacherDocument.objects.filter(id__in=selected, teacher=request.user).delete()
    return redirect('teacher_files')    
# =========== #
#   TESTING   # ======================= #
# =========== #

# UPLOAD FILE 
def upload_file(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('myApp/file_list.html')  
    else:
        form = DocumentForm()
    
    return render(request, 'myApp/upload.html', {'form': form})

# LIST FILE UPLOADED 
def file_list(request):
    documents = Document.objects.all()
    return render(request, 'myApp/file_list.html', {'documents': documents})


# TESTING DATA
def testingData(request):
    context={}
    context['title'] = 'Testing Data'
    return render(request, "myApp/testingData.html", context)
