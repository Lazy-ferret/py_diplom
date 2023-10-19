from django.http import HttpResponse
from django.shortcuts import render


# test views
def hello_view(request):
    return HttpResponse("hello world")
