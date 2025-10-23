
from django.urls import path
from . import views   

urlpatterns = [
<<<<<<< HEAD
    path('', views.index), 
    path('register/', views.showRegister),
    path('register_user/', views.showRegisterUser),
    path('register_doctor/', views.showRegisterDoctor),
    path('login/', views.login),
    path('doctors/', views.showDoctors),   
    path('appointments/', views.showAppoitments), 
    path('home/', views.showHome),
    path('history/', views.showHistory),
    path('chatbot/', views.showChatBot),
=======
    path('', views.index, name='i`ndex'), 
>>>>>>> 9888c11990d89aa25db034f0809a281d32dd9d58
]
