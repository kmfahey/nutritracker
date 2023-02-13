#!/usr/bin/python3

from django.urls import path

from . import views

urlpatterns = [
    path('',                                                                views.recipes,                                           name='recipes'),
    path('search',                                                          views.search,                                            name='recipes_search'),
    path('search/',                                                         views.search,                                            name='recipes_search_slash'),
    path('search_results',                                                  views.search_results,                                    name='recipes_search_results'),
    path('search_results/',                                                 views.search_results,                                    name='recipes_search_results_slash'),
#    path('builder/new',                                                     views.builder_new,                                       name='recipes_builder_new'
#    path('builder/new/',                                                    views.builder_new,                                       name='recipes_builder_new_slash'
#    path('builder/<str:mongodb_id>',                                        views.builder_mongodb_id,                                name='recipes_builder_mongodb_id'
#    path('builder/<str:mongodb_id>/',                                       views.builder_mongodb_id,                                name='recipes_builder_mongodb_id_slash'
#    path('builder/<str:mongodb_id>/ingredients/add',                        views.builder_mongodb_id_ingredients_add,                name='recipes_builder_mongodb_id_ingredients_add'
#    path('builder/<str:mongodb_id>/ingredients/add/',                       views.builder_mongodb_id_ingredients_add,                name='recipes_builder_mongodb_id_ingredients_add_slash'
#    path('builder/<str:mongodb_id>/ingredients/<int:fdc_id>/add',           views.builder_mongodb_id_ingredients_fdc_id_add,         name='recipes_builder_mongodb_id_ingredients_fdc_id_add'
#    path('builder/<str:mongodb_id>/ingredients/<int:fdc_id>/add/',          views.builder_mongodb_id_ingredients_fdc_id_add,         name='recipes_builder_mongodb_id_ingredients_fdc_id_add_slash'
#    path('builder/<str:mongodb_id>/ingredients/<int:fdc_id>/add/confirm',   views.builder_mongodb_id_ingredients_fdc_id_add_confirm, name='recipes_builder_mongodb_id_ingredients_fdc_id_add_confirm'
#    path('builder/<str:mongodb_id>/ingredients/<int:fdc_id>/add/confirm/',  views.builder_mongodb_id_ingredients_fdc_id_add_confirm, name='recipes_builder_mongodb_id_ingredients_fdc_id_add_confirm_slash'
#    path('builder/<str:mongodb_id>/finished',                               views.builder_mongodb_id_finished,                       name='recipes_builder_mongodb_id_finished'
#    path('builder/<str:mongodb_id>/finished/',                              views.builder_mongodb_id_finished,                       name='recipes_builder_mongodb_id_finished_slash'
    path('<str:mongodb_id>',                                                views.recipes_mongodb_id,                                name='recipes_mongodb_id'),
    path('<str:mongodb_id>/',                                               views.recipes_mongodb_id,                                name='recipes_mongodb_id_slash'),
]
