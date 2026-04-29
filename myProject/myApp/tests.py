from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.urls import reverse
from django.test import TestCase
from myApp.models import TeacherLoginHistory, Student, Exam, Teacher, Mark, StudentPersonal, Subject, Classroom, User


@receiver(user_logged_in)
def log_teacher_login(sender, request, user, **kwargs):
    if hasattr(user, "teacherprofile"):
        TeacherLoginHistory.objects.create(teacher=user)
        
class PredictionViewTest(TestCase):
    def setUp(self):
        # Create necessary data for test student, teacher, subject, exam, etc.
        classroom = Classroom.objects.create(name="1 Cempaka", form_level="Form 1")
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        teacher = Teacher.objects.create(
            user=self.user,
            name="Test Teacher",
            race="Malay",
            email="teacher@example.com",
            phone_number="0123456789",
            address="Test Address",
            gender="Male",
            ic_number="123456789012",
            age=35,
            intake="2024",
            number_matric_teach="20140102",
            assigned_class=classroom,
            username='testuser',
            password='testpassword',
        )
        subject = Subject.objects.create(name="Math", form_level="Form 1")
        student = Student.objects.create(
            full_name="Ali Bin Abu",
            nickname="Ali",
            ic_number="111122223333",
            age=15,
            gender="Male",
            race="Malay",
            address="Test Address",
            intake="2024",
            number_matric_std="20240201",
            student_class=classroom,
            guardian_name="Abu Bin Ahmad",
            guardian_contact="0121112233",
            guardian_email="parent@example.com",
            registered_by=teacher,
        )
        exam = Exam.objects.create(name="1st Exam", year=2024, date="2024-03-01")
        Mark.objects.create(student=student, subject=subject, exam=exam, marks=75)
        StudentPersonal.objects.create(
            student=student,
            exam=exam,
            address="U",
            famsize="B40",
            pstatus="T",
            mjob="teacher",
            fjob="teacher",
            guardian="father",
            famsup="yes",
            traveltime=2,
            studytime=3,
            merit=2,
            activities=1,
            internet=2,
            famrel=4,
            freetime=3,
            goout=2,
            health=4,
            medu=5,
            fedu=5,
        )
        self.student = student

    def test_prediction_view(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse("view_student_result", kwargs={"student_id": self.student.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("prediction_result", response.context)