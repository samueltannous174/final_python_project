from django.shortcuts import render
from .models import *
from django.contrib import messages
from django.shortcuts import redirect
import bcrypt

from django.http import HttpResponse

def login(request):
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
    context = {
        'doctors': get_all_doctors()
    }

    return render(request,'doctors.html',context)

def showHistory(request):
    return render(request,'history_case.html')

def showChatBot(request):
    return render(request,'chatbot.html')

def showLogin(request):
    return render(request,'login.html')


def RegisterUser(request):
    print(request.POST)
    if request.method == 'POST':
        errors = User.objects.register_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg, extra_tags='login')
            if request.POST['role'] == 'patient':
                return redirect('/register_user')
            elif request.POST['role'] == 'doctor':
                return redirect('/register_doctor')
        hashed = bcrypt.hashpw(request.POST['password'].encode(), bcrypt.gensalt()).decode()
        user= create_user_with_role(request.POST,hashed)
        request.session['id'] = user.id
        request.session['name'] = user.first_name

        return redirect('/home')

    return redirect('/')


def loginSubmit(request):
    print(request.POST)
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
        return redirect('/home')

    return redirect('/')


def filterDoctors(request):
    query = ""
    if request.method == "POST":
        query = request.POST.get("q", "").strip()

    doctors = filter_doctors(query)
    return render(request, "doctors.html", {"doctors": doctors, "query": query})




def logout(request):
    request.session.flush()
    messages.success(request, "You have been logged out.", extra_tags='login')
    return redirect('/')