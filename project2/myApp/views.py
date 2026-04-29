from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse # type: ignore
from .service import TaskManager

tm = TaskManager()

def add_task_view(request):
    try:
        tm.add_task(1, "Sample Task")
        return JsonResponse({"message": "Task added successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)})

def remove_task_view(request):
    try:
        tm.remove_task(1)
        return JsonResponse({"message": "Task removed successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)})

def complete_task_view(request):
    try:
        tm.mark_task_complete(1)
        return JsonResponse({"message": "Task marked as complete"})
    except Exception as e:
        return JsonResponse({"error": str(e)})

def list_tasks_view(request):
    try:
        data = tm.list_pending_tasks()
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)})