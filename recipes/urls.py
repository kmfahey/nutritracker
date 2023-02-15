#!/usr/bin/python3

from django.urls import path

from . import views

urlpatterns = [
    path('',                                                                views.recipes,                                           name='recipes'),
    path('search',                                                          views.search,                                            name='recipes_search'),
    path('search/',                                                         views.search,                                            name='recipes_search_slash'),
    path('search_results',                                                  views.search_results,                                    name='recipes_search_results'),
    path('search_results/',                                                 views.search_results,                                    name='recipes_search_results_slash'),
    path('builder',                                                         views.builder,                                           name='recipes_builder'),
    path('builder/',                                                        views.builder,                                           name='recipes_builder_slash'),
    path('builder/new',                                                     views.builder_new,                                       name='recipes_builder_new'),
    path('builder/new/',                                                    views.builder_new,                                       name='recipes_builder_new_slash'),
    path('builder/<str:mongodb_id>',                                        views.builder_mongodb_id,                                name='recipes_builder_mongodb_id'),
    path('builder/<str:mongodb_id>/',                                       views.builder_mongodb_id,                                name='recipes_builder_mongodb_id_slash'),
    path('builder/<str:mongodb_id>/add_ingredient',                         views.builder_mongodb_id_add_ingredient,                 name='recipes_builder_mongodb_id_add_ingredient'),
    path('builder/<str:mongodb_id>/add_ingredient/',                        views.builder_mongodb_id_add_ingredient,                 name='recipes_builder_mongodb_id_add_ingredient_slash'),
    path('builder/<str:mongodb_id>/add_ingredient/<int:fdc_id>',            views.builder_mongodb_id_add_ingredient_fdc_id,          name='recipes_builder_mongodb_id_add_ingredient_fdc_id'),
    path('builder/<str:mongodb_id>/add_ingredient/<int:fdc_id>/',           views.builder_mongodb_id_add_ingredient_fdc_id,          name='recipes_builder_mongodb_id_add_ingredient_fdc_id_slash'),
    path('builder/<str:mongodb_id>/remove_ingredient',                      views.builder_mongodb_id_remove_ingredient,              name='recipes_builder_mongodb_id_remove_ingredient'),
    path('builder/<str:mongodb_id>/remove_ingredient/',                     views.builder_mongodb_id_remove_ingredient,              name='recipes_builder_mongodb_id_remove_ingredient_slash'),
    path('builder/<str:mongodb_id>/add_ingredient/<int:fdc_id>/confirm',    views.builder_mongodb_id_add_ingredient_fdc_id_confirm,  name='recipes_builder_mongodb_id_add_ingredient_fdc_id_confirm'),
    path('builder/<str:mongodb_id>/add_ingredient/<int:fdc_id>/confirm/',   views.builder_mongodb_id_add_ingredient_fdc_id_confirm,  name='recipes_builder_mongodb_id_add_ingredient_fdc_id_confirm_slash'),
    path('builder/<str:mongodb_id>/finish',                                 views.builder_mongodb_id_finish,                         name='recipes_builder_mongodb_id_finish'),
    path('builder/<str:mongodb_id>/finish/',                                views.builder_mongodb_id_finish,                         name='recipes_builder_mongodb_id_finish_slash'),
    path('builder/<str:mongodb_id>/delete',                                 views.builder_mongodb_id_delete,                         name='recipes_builder_mongodb_id_delete'),
    path('builder/<str:mongodb_id>/delete/',                                views.builder_mongodb_id_delete,                         name='recipes_builder_mongodb_id_delete_slash'),
    path('<str:mongodb_id>',                                                views.recipes_mongodb_id,                                name='recipes_mongodb_id'),
    path('<str:mongodb_id>/',                                               views.recipes_mongodb_id,                                name='recipes_mongodb_id_slash'),
]
