
from django.db import models
from django.contrib.auth.models import User
import re




class User(models.Model):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('admin', 'Admin'),
    ]
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)  
    role = models.CharField(max_length=45, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    photo = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
    

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=255)
    years_of_experience = models.PositiveIntegerField()
    bio = models.TextField(blank=True, null=True)
    avalibilty = models.CharField(max_length=255)
    certificate = models.TextField(blank=True, null=True)



    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"



class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    age = models.PositiveIntegerField()
    blood_type = models.CharField(max_length=3)
    blood_pressure = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name()



class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateTimeField()
    reason = models.CharField(max_length=255)
    is_finished = models.BooleanField(default=False)

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

    def __str__(self):
        return f"{self.title} ({self.patient.user.last_name})"





