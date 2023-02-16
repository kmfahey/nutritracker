#!/usr/bin/python3

from django.urls import path

from . import views

urlpatterns = [
    path('/tracker',      views.tracker,     name='tracker'),
    path('/tracker/',     views.tracker,     name='tracker_slash'),
    path('/tracker/add',  views.tracker_add, name='tracker_add'),
    path('/tracker/add/', views.tracker_add, name='tracker_add_slash'),
]
