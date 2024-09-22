from django.shortcuts import render
from django.http import HttpResponse,HttpRequest
# Create your views here.
def t(request):
    return HttpResponse("hello world")