from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.register),
    path('login', views.login),
    path('logout', views.logout),
    path('updateProfile', views.updateProfile),
    path('index', views.Authentication),
]