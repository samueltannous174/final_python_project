from django.urls import path
from . import views   

urlpatterns = [
    path('', views.showHome), 
    path('register/', views.showRegister),
    path('register_user/', views.showRegisterUser),
    path('register_doctor/', views.showRegisterDoctor),
    path('login/', views.login),
    path('doctors/', views.showDoctors),   
    path('appointments/', views.showAppoitments), 
    path('home/', views.showHome),
    path('history/', views.showHistory),
    path('chatbot/', views.showChatBot),
    path ('register_user_submit/', views.RegisterUser),
    path ('login_submit/', views.loginSubmit),
    path ('logout/', views.logout),
    path ('filter_doctors/', views.filterDoctors),
    path('patients/', views.showPatients),
    path('patient/<int:id>/', views.showPatientDetails)
]
