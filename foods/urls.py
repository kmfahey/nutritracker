#!/usr/bin/python3

from django.urls import path

from . import views

urlpatterns = [
    path('',                         views.foods,                name='foods'),
    path('<int:fdc_id>',             views.foods_fdc_id,         name='foods_+fdc_id+'),
    path('<int:fdc_id>/',            views.foods_fdc_id,         name='foods_+fdc_id+_slash'),
    path('local_search',             views.local_search,         name='foods_local_search'),
    path('local_search/',            views.local_search,         name='foods_local_search_slash'),
    path('local_search_results',     views.local_search_results, name='foods_local_search_results'),
    path('local_search_results/',    views.local_search_results, name='foods_local_search_results_slash'),
    path('fdc_search',               views.fdc_search,           name='foods_fdc_search'),
    path('fdc_search/',              views.fdc_search,           name='foods_fdc_search_slash'),
    path('fdc_search_results',       views.fdc_search_results,   name='foods_fdc_search_results'),
    path('fdc_search_results/',      views.fdc_search_results,   name='foods_fdc_search_results_slash'),
    path('fdc_search/<int:fdc_id>',  views.fdc_search_fdc_id,    name='foods_fdc_search_+fdc_id+'),
    path('fdc_search/<int:fdc_id>/', views.fdc_search_fdc_id,    name='foods_fdc_search_+fdc_id+_slash'),
    path('fdc_import',               views.fdc_import,           name='foods_fdc_import'),
    path('fdc_import/',              views.fdc_import,           name='foods_fdc_import_slash')
]
