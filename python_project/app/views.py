from . import models
from django.shortcuts import render, redirect
from django.contrib import messages
import bcrypt
from datetime import date, datetime, time, timedelta
from calendar import Calendar, month_name
from django.utils import timezone
from urllib.parse import urlencode

def user_details(id):
    return models.get_user(id)


def login(request):
    return render(request,'login.html')

def showRegister(request):
    return render(request,'register.html')

def showRegisterUser(request):
    return render(request,'register_user.html')

def showRegisterDoctor(request):
    return render(request,'register_doctor.html')

def showPatientDetails(request, id):
    print(id)
    print(request.GET['doctor_id'])
    doctor = models.get_user(request.GET['doctor_id'])
    patient = models.get_user(id)
    cases = models.get_all_patient_cases(id)
    context = {
        'user': doctor,
        'patient': patient,
        'details': patient.patient_profile,
        'cases': cases
    }
    return render(request, 'patient_details.html', context)

def  showHome(request):
    if 'id' not in request.session:
        return render(request,'dashboard_login_register.html')
    
    context = {
        'user': user_details(request.session['id'])
    }
    return render(request,'dashboard_login_register.html', context)

def showPatients(request):
    if 'id' not in request.session:
        return redirect('/login')
    context = {
        'patients': models.get_all_patients(request.session['id']),
        'user': user_details(request.session['id'])
    }
    return render(request, 'patients.html', context)

def showDoctors(request):
    if 'id' not in request.session:
        return redirect('/login')
    context = {
        'doctors': models.get_all_doctors(),
        'user': user_details(request.session['id'])
    }
    return render(request,'doctors.html',context)

def showHistory(request):
    if 'id' not in request.session:
        return redirect('/login')
    context = {
        'user': user_details(request.session['id'])
    }
    return render(request,'history_case.html', context)

def showChatBot(request):
    if 'id' not in request.session:
        return redirect('/login')
    context = {
        'user': user_details(request.session['id'])
    }
    return render(request,'chatbot.html', context)

def showLogin(request):
    
    return render(request,'login.html')


def RegisterUser(request):
    print(request.POST)
    if request.method == 'POST':
        errors = models.User.objects.register_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg, extra_tags='login')
            if request.POST['role'] == 'patient':
                return redirect('/register_user')
            elif request.POST['role'] == 'doctor':
                return redirect('/register_doctor')
        hashed = bcrypt.hashpw(request.POST['password'].encode(), bcrypt.gensalt()).decode()
        user= models.create_user_with_role(request.POST,hashed)
        request.session['id'] = user.id
        return redirect('/home')

    return redirect('/')


def loginSubmit(request):
    print(request.POST)
    if request.method == 'POST':
        errors = models.User.objects.login_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg, extra_tags='login')
            return redirect('/login')
        
        user = models.login_user(request.POST)
        request.session['id'] = user.id
        
        messages.success(request, f"Welcome back, {user.first_name}!", extra_tags='login')
        return redirect('/home')

    return redirect('/')


def filterDoctors(request):
    query = ""
    if request.method == "POST":
        query = request.POST.get("q", "").strip()

    doctors = models.filter_doctors(query)
    return render(request, "doctors.html", {"doctors": doctors, "query": query})




def logout(request):
    request.session.flush()
    messages.success(request, "You have been logged out.", extra_tags='login')
    return redirect('/')




def showAppoitments(request):
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    day_param = request.GET.get("day")
    
    doctor_id = request.POST.get("doctor") or request.GET.get("doctor")
    
    cal = Calendar(firstweekday=6)
    weeks = cal.monthdatescalendar(year, month)
    
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    
    selected_day = None
    if day_param:
        try:
            selected_day = date(year, month, int(day_param))
        except ValueError:
            selected_day = None
    
    time_slots = [time(h, 0) for h in range(9, 15)]
    
    doctor = models.Doctor.objects.filter(pk=doctor_id).first() if doctor_id else None
    if not doctor:
        doctor = models.Doctor.objects.first() 
    if not doctor_id and doctor:
        doctor_id = str(doctor.pk)

    user_patient_pk =  request.session.get("id")
    print(user_patient_pk)
    user = models.User.objects.get(pk=user_patient_pk)
    print(user)
    patient = getattr(user, "patient_profile", None)
    print(patient)

    

    appointments_for_day = []
    booked_slots = set()
    tz = timezone.get_current_timezone()

    def redirect_same(_year: int, _month: int, _day: int | None):
        params = {"year": _year, "month": _month}
        if _day is not None:
            params["day"] = _day
        if doctor_id:
            params["doctor"] = doctor_id
        return redirect(f"{request.path}?{urlencode(params)}")

    if selected_day:
        start_dt = datetime.combine(selected_day, time(0, 0), tzinfo=tz)
        end_dt = start_dt + timedelta(days=1)

        appointments_for_day = (
            models.Appointment.objects
            .filter(date__gte=start_dt, date__lt=end_dt)
            .select_related("doctor", "patient")
            .order_by("date")
        )
        for appt in appointments_for_day:
            booked_slots.add(appt.date.strftime("%H:%M"))

    if request.method == "POST":
        if not selected_day:
            messages.error(request, "Please select a day first.")
            return redirect_same(year, month, None)

        slot = request.POST.get("time_slot")
        if not slot:
            messages.error(request, "Missing time slot.")
            return redirect_same(year, month, selected_day.day)

        try:
            slot_time = time.fromisoformat(slot)
        except ValueError:
            messages.error(request, "Invalid time slot.")
            return redirect_same(year, month, selected_day.day)

        appointment_dt = datetime.combine(selected_day, slot_time, tzinfo=tz)

        if models.Appointment.objects.filter(date=appointment_dt).exists():
            messages.warning(request, "That time is already booked.")
            return redirect_same(year, month, selected_day.day)

        print(doctor, patient)
        if not doctor or not patient:
            messages.error(request, "Doctor or patient not configured.")
            return redirect_same(year, month, selected_day.day)

        models.Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            date=appointment_dt,
            reason="General Checkup",
        )
        messages.success(request, f"Appointment created at {appointment_dt.strftime('%I:%M %p')}.")
        return redirect_same(year, month, selected_day.day)

    context = {
        "doctor_id": doctor_id,
        "doctor_pk": doctor.pk if doctor else None,
        "year": year,
        "month": month,
        "month_label": f"{month_name[month]} {year}",
        "weeks": weeks,
        "today": today,
        "selected_day": selected_day,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "time_slots": time_slots,
        "appointments_for_day": appointments_for_day,
        "booked_slots": booked_slots,
        "doctor_id": doctor_id,
    }
    return render(request, "appointment.html", context)

def addCase(request):
    if request.method == 'GET':
        return redirect(f'/patient/{request.POST['patient_id']}')
    if request.method == 'POST':
        print(request.POST)
        errors = models.MedicalCase.objects.case_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg)
            print(f"request.POST['patient_id'] = {request.POST['patient_id']}")
            return redirect(f'/patient/{request.POST['patient_id']}')
    case = models.add_case(request.POST)
    return redirect(f'/patient/{request.POST['patient_id']}')