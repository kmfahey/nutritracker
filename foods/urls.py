#!/usr/bin/python3

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:fdc_id>', views.display_food),
    path('<int:fdc_id>/', views.display_food),
    path('local_search', views.local_search),
    path('local_search/', views.local_search),
    path('local_search_results', views.local_search_results),
    path('local_search_results/', views.local_search_results),
    path('fdc_search', views.fdc_search),
    path('fdc_search/', views.fdc_search),
    path('fdc_search_results', views.fdc_search_results),
    path('fdc_search_results/', views.fdc_search_results)
]

