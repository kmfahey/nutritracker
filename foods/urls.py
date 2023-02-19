#!/usr/bin/python3

from django.urls import path

from . import views

urlpatterns = [
    path('',                         views.foods,                      name='foods'),
    path('<int:fdc_id>',             views.foods_fdc_id,               name='foods_+fdc_id+'),
    path('<int:fdc_id>/',            views.foods_fdc_id,               name='foods_+fdc_id+_slash'),
    path('local_search',             views.foods_local_search,         name='foods_local_search'),
    path('local_search/',            views.foods_local_search,         name='foods_local_search_slash'),
    path('local_search_results',     views.foods_local_search_results, name='foods_local_search_results'),
    path('local_search_results/',    views.foods_local_search_results, name='foods_local_search_results_slash'),
    path('fdc_search',               views.foods_fdc_search,           name='foods_fdc_search'),
    path('fdc_search/',              views.foods_fdc_search,           name='foods_fdc_search_slash'),
    path('fdc_search_results',       views.foods_fdc_search_results,   name='foods_fdc_search_results'),
    path('fdc_search_results/',      views.foods_fdc_search_results,   name='foods_fdc_search_results_slash'),
    path('fdc_search/<int:fdc_id>',  views.foods_fdc_search_fdc_id,    name='foods_fdc_search_+fdc_id+'),
    path('fdc_search/<int:fdc_id>/', views.foods_fdc_search_fdc_id,    name='foods_fdc_search_+fdc_id+_slash'),
    path('fdc_import',               views.foods_fdc_import,           name='foods_fdc_import'),
    path('fdc_import/',              views.foods_fdc_import,           name='foods_fdc_import_slash'),
    path('add_food',                 views.foods_add_food,             name='foods_add_food'),
    path('add_food/',                views.foods_add_food,             name='foods_add_food_slash')
]
