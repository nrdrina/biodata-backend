from . import views
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from .views import homepage_redirect, upload_file, file_list
# from weasyprint import HTML

urlpatterns = [
    ################
    # TEACHER SUB MENU
    path('', homepage_redirect, name='homepage'),  # <=== ADD THIS for default redirect
    path('loginTeach/', views.loginTeach, name='loginTeach'),
    path('teacher_logout/', views.logout_teacher, name='teacher_logout'),
    path('homeTeach/', include(([
        path('', views.homeTeach, name='homeTeach'),
        path("profileTeach/", views.profileTeach, name="profileTeach"),
        path('stdRecord/', views.stdRecord, name='stdRecord'),
        path('subMark/', views.subject_marking, name='subMark'),
        path("academic-calendar/teacher/", views.academic_calendar_teacher, name="academicCalendarTeach"),
        path('attendance/', views.take_attendance, name='take_attendance'),
        path('ranking/', views.student_ranking, name='stdRanking'),
        path('files/', views.teacher_files, name='teacher_files'),

    ]))),
    # path('newStd/', views.registerStudent, name='newStd'),
    path('ranking/pdf/<int:student_id>/<str:exam_type>/', views.download_predict_pdf, name='download_predict_pdf'),
    path('files/delete/', views.delete_teacher_file, name='delete_teacher_file'),
    path('stdRecordView/<int:student_id>/', views.view_student_record, name='stdRecordView'),
    path('subEntryMarkAndPersonal/<int:student_id>/', views.enter_mark_and_personal, name='subEntryMarkAndPersonal'),
    path('result/<int:student_id>/', views.view_student_result, name='view_student_result'),

    ################
    # ADMIN SUB MENU
    path('loginAdmin/', views.loginAdmin, name='loginAdmin'),
    path('admin_logout/', views.logout_admin, name='admin_logout'),
    path('homeAdmin/', include([
        path('', views.homeAdmin, name='homeAdmin'),
        path("profileAdmin/", views.profile_admin, name="profileAdmin"),
        path('manageTeach/', views.manageTeach, name='manageTeach'),
        path("manageParent/", views.manageParent, name="manageParent"),
        path("manageStd/", views.manageStd, name="manageStd"),
        path("subjectStats/", views.subject_statistics, name="subjectStats"),
        path("gradePerformance/", views.grade_distribution_view, name="gradePerformance"),
        path("academic-calendar/admin/", views.uploadDocument, name="academic_document_admin"),
        path('prediction-report/', views.prediction_dashboard, name='prediction'),

    ])),

    path("academic-calendar/delete/", views.delete_academic_files, name="delete_academic_files"),
    path("gradePerformance/export", views.export_grade_performance_pdf, name="export_grade_performance_pdf"),
    path("subjectStats/export/", views.export_subject_stats_pdf, name="export_subject_stats_pdf"),
    path("profileAdmin/edit/", views.edit_profile_admin, name="editProfileAdmin"),
    path('manageStdView/<int:student_id>/', views.view_student, name='manageStdView'),
    path("manageParentView/<int:parent_id>/", views.manageParentView, name="manageParentView"),
    path('deleteStudent/<int:student_id>/', views.delete_student, name='delete_student'),
    path('deleteTeacher/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'), 
    path('deleteParent/<int:user_id>/', views.delete_parent, name='delete_parent'),
    path('manageTeachView/<int:teacher_id>/', views.view_teacher, name='manageTeachView'),
    path('newTeach/', views.newTeach, name='newTeach'),
    path("newParents/", views.newParents, name="newParents"),
    path('register-student/', views.register_student_by_admin, name='newStd'),
    path('resetPassTeach/', views.resetPassTeach, name='resetPassTeach'),
    path('resetPassParent/', views.resetPassParent, name='resetPassParent'),
    
    
    ################
    # PARENT SUB MENU
    path('loginParent/', views.loginParent, name='loginParent'),
    path('parent_logout/', views.logout_parent, name='parent_logout'),
    path('homeParent/', views.homeParent, name='homeParent'),
    path("export-exam-pdf/", views.export_exam_pdf, name="export_exam_pdf"),
    path("request-child-add/", views.request_child_add, name="request_child_add"),
    
    
    #########
    # Testing
    path('testingData/', views.testingData, name='testingData'),
    path('upload/', upload_file, name='upload_file'),
    path('files/', file_list, name='file_list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
