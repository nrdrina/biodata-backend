from django.urls import path # type: ignore
from . import views

urlpatterns = [
    path('add/', views.add_task_view),
    path('remove/', views.remove_task_view),
    path('complete/', views.complete_task_view),
    path('list/', views.list_tasks_view),
]