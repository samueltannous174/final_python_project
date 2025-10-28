
from django.db import models
from django.contrib.auth.models import User
import re
import bcrypt
from django.db.models import Q

EMAIL_RE = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
PHONE_RE = re.compile(r'^\+?[0-9]{7,15}$')
BLOOD_TYPES = {'A+','A-','B+','B-','AB+','AB-','O+','O-'}
BP_RE = re.compile(r'^\d{2,3}/\d{2,3}$')







class UserManager(models.Manager):
    def register_validator(self, postData):

        errors = {}
        email = (postData.get('email') or '').strip().lower()
        first = (postData.get('first_name') or '').strip()
        last = (postData.get('last_name') or '').strip()
        pw = postData.get('password') or ''
        cpw = postData.get('confirm') or ''
        role = (postData.get('role') or '').strip().lower()
        phone = (postData.get('phone') or '').strip()

        if email and self.model.objects.filter(email__iexact=email).exists():
            errors['email'] = 'Email already exists.'

        if len(first) < 2:
            errors['first_name'] = 'First name should be at least 2 characters.'

        if len(last) < 2:
            errors['last_name'] = 'Last name should be at least 2 characters.'

        if not EMAIL_RE.match(email or ''):
            errors['email'] = 'Please enter a valid email address.'

        if phone and not PHONE_RE.match(phone):
            errors['phone'] = "Phone must be 7–15 digits, optionally starting with '+'."
        
        if len(pw) < 8:
            errors['password'] = 'Password must be at least 8 characters.'

        if pw != cpw:
            errors['confirmPassword'] = 'Passwords do not match.'

        return errors


    def login_validator(self, postData):

        errors = {}
        email = (postData.get('email') or '').strip().lower()
        pw = postData.get('password') or ''

        from .models import User 
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            errors['login'] = 'Invalid email or password.'
            return errors

        try:
            hashed = user.password.encode() if isinstance(user.password, str) else user.password
            if not bcrypt.checkpw(pw.encode(), hashed):
                errors['login'] = 'Invalid email or password.'
        except Exception:
            errors['login'] = 'Invalid email or password.'


        return errors
    



class MedicalCaseManager(models.Manager):
    def case_validator(self, post):
        errors = {}
        doctor_id = post['doctor_id']
        patient_id = post['patient_id']
        if not doctor_id or not patient_id:
            errors['user'] = 'User and Patient is required.'
        else:
            if post['symptoms'] == '':
                errors['symptoms'] = "Symptoms should not be empty"
            if post['title'] == '':
                errors['title'] = "Tilte should not be empty"
        
        return errors



class DoctorManager(models.Manager):
    def create_validator(self, postData):
    
        errors = {}

        specialization = (postData.get('specialization') or '').strip()
        yoe_raw = postData.get('years_of_experience')
        bio = (postData.get('bio') or '').strip()

        if not specialization:
            errors['specialization'] = 'Specialization is required.'
        if specialization not in ('Dermatology', 'General Surgery', 'Neurology', 'Allergist'):
            errors['specialization'] = 'Specialization must be one of A, B, C, D, or E.'

        if not bio or len(bio) < 10:
            errors['bio'] = 'Bio must be at least 10 characters.'

        try:
            yoe = int(yoe_raw)
            if yoe < 0 or yoe > 80:
                errors['years_of_experience'] = 'Years of experience must be between 0 and 80.'
        except (TypeError, ValueError):
            errors['years_of_experience'] = 'Years of experience must be an integer.'


        return errors
    

class PatientManager(models.Manager):
    def create_validator(self, postData):

        errors = {}

        age_raw = postData.get('age')
        blood_type = (postData.get('blood_type') or '').strip().upper()
        blood_pressure = (postData.get('blood_pressure') or '').strip()
        print(blood_pressure)

        try:
            age = int(age_raw)
            if age < 1 or age > 120:
                errors['age'] = 'Age must be between 1 and 120.'
            
        except (TypeError, ValueError):
            errors['age'] = 'Age must be an integer.'

        if blood_type not in BLOOD_TYPES:
            errors['blood_type'] = 'Invalid blood type.'

        if blood_pressure and not BP_RE.match(blood_pressure):
            errors['blood_pressure'] = "Blood pressure must look like '120/80'."

        return errors


class MedicalCaseManager(models.Manager):
    def case_validator(self, post):
        errors = {}
        doctor_id = post['doctor_id']
        patient_id = post['patient_id']
        if not doctor_id or not patient_id:
            errors['user'] = 'User and Patient is required.'
        else:
            if post['symptoms'] == '':
                errors['symptoms'] = "Symptoms should not be empty"
            if post['title'] == '':
                errors['title'] = "Tilte should not be empty"
        
        return errors



class User(models.Model):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('admin', 'Admin'),
    ]
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)  
    role = models.CharField(max_length=45, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    photo = models.TextField(blank=True, null=True)
    objects = UserManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"
    

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=255)
    years_of_experience = models.PositiveIntegerField()
    bio = models.TextField(blank=True, null=True)
    availability = models.CharField(max_length=255, default='Available')
    certificate = models.TextField(blank=True, null=True)
    objects = DoctorManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.specialization}"


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    age = models.PositiveIntegerField()
    blood_type = models.CharField(max_length=3)
    blood_pressure = models.CharField(max_length=20, blank=True, null=True)
    objects = PatientManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.first_name



class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateTimeField()
    reason = models.CharField(max_length=255)
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.user.last_name} and {self.patient.user.last_name} on {self.date}"



class MedicalCase(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_cases')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='medical_cases')
    title = models.CharField(max_length=255)
    symptoms = models.TextField()
    diagnosis = models.TextField(blank=True, null=True)
    treatment = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    objects = MedicalCaseManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.patient.user.last_name})"

def create_user_with_role(data,hashed):
    role = data.get('role', '').lower().strip()

    user = User.objects.create(
            email=data['email'].strip().lower(),
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            password=hashed,
            role=role,
            phone=(data.get('phone') or '').strip() or None,
        )

    if role == 'doctor':
            Doctor.objects.create(
                user=user,
                specialization=data.get('specialization', '').strip(),
                years_of_experience=int(data.get('years_of_experience', 0)),
                bio=(data.get('bio') or '').strip() or None,
                availability=(data.get('availability') or data.get('avalibilty') or '').strip(),
                certificate=(data.get('certificate') or '').strip() or None,
            )

    elif role == 'patient':
            Patient.objects.create(
                user=user,
                age=int(data.get('age', 0)),
                blood_type=data.get('blood_type', '').strip().upper(),
                blood_pressure=(data.get('blood_pressure') or '').strip() or None,
            )

    return user


def login_user(data):
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return None

    try:
        hashed = user.password.encode() if isinstance(user.password, str) else user.password
        if not bcrypt.checkpw(password.encode(), hashed):
            return None
    except Exception:
        return None

    return user


def  get_all_doctors():
    return Doctor.objects.all()


def filter_doctors(query: str = ""):
    doctors = Doctor.objects.select_related('user')

    if query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(specialization__icontains=query)
        )

    return doctors

def get_user(id):
    return User.objects.get(id = id)

def get_doctor(id):
    return Doctor.objects.get(id = id)

def get_all_patients(doctor_id):
    user = get_user(doctor_id)
    doctor = user.doctor_profile
    patients = Patient.objects.filter(appointments__doctor = doctor).distinct()
    print("pattients")
    print(patients)

    return patients

def add_case(post):
    print(post['doctor_id'])
    doctor = get_user(post['doctor_id'])
    patient = get_user(post['patient_id'])  
    return MedicalCase.objects.create(title = post['title'], symptoms = post['symptoms'], diagnosis = post['diagnosis'], treatment = post['treatment'], reason = post['reason'], doctor = doctor.doctor_profile, patient = patient.patient_profile)

def get_all_patient_cases(user_id):
    user = get_user(user_id)
    patient = user.patient_profile
    return patient.medical_cases.all()