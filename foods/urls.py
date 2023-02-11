#!/usr/bin/python3

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:fdc_id>', views.display_food),
    path('<int:fdc_id>/', views.display_food)
]

