from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Biodata
from .serializers import BiodataSerializer

def home(request):
    if request.method == "POST":
        name = request.POST.get("name")
        age = request.POST.get("age")
        email = request.POST.get("email")

        Biodata.objects.create(
            name=name,
            age=age,
            email=email
        )

        return JsonResponse({"message": "Saved to DB"})

    return render(request, "biodata/form.html")

# API Views
@api_view(['GET', 'POST'])
def biodata_api(request):

    if request.method == 'GET':
        data = Biodata.objects.all()
        serializer = BiodataSerializer(data, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = BiodataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
@api_view(['PUT', 'DELETE'])
def biodata_detail(request, id):

    try:
        biodata = Biodata.objects.get(id=id)
    except Biodata.DoesNotExist:
        return Response({"error": "Not found"})

    if request.method == 'PUT':
        serializer = BiodataSerializer(biodata, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    if request.method == 'DELETE':
        biodata.delete()
        return Response({"message": "Deleted successfully"})
        
        
def view_biodata(request):
    data = list(Biodata.objects.values())
    return JsonResponse(data, safe=False)