from django.shortcuts import render
from .models import *
from django.contrib import messages
from django.shortcuts import redirect

# Create your views here.

from django.http import HttpResponse

def index(request):
    return render(request,'login.html')

def showRegister(request):
    return render(request,'register.html')

def showRegisterUser(request):
    return render(request,'register_user.html')

def showRegisterDoctor(request):
    return render(request,'register_doctor.html')

def showAppoitments(request):
    return render(request,'appointment.html')

def  showHome(request):
    return render(request,'dashboard_login_register.html')

def showDoctors(request):
    return render(request,'doctors.html')

def showHistory(request):
    return render(request,'history_case.html')

def showChatBot(request):
    return render(request,'chatbot.html')

def register(request):
    if request.method == 'POST':
        errors = User.objects.Register_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg, extra_tags='register')
            return redirect('/')
        
        create_user(request.POST)

        messages.success(request, "Registration successful! You can now log in.", extra_tags='register')
        return redirect('/')
    return redirect('/')


def showLogin(request):
    return render(request,'login.html')
def login(request):
    if request.method == 'POST':
        errors = User.objects.login_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg, extra_tags='login')
            return redirect('/')

        user = login_user(request.POST)

        request.session['id'] = user.id
        request.session['name'] = user.first_name
        messages.success(request, f"Welcome back, {user.first_name}!", extra_tags='login')
        return redirect('/success')

    return redirect('/')
