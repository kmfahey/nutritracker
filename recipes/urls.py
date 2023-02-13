#!/usr/bin/python3

from django.urls import path

from . import views

urlpatterns = [
    path('',                                 views.recipes,                          name='recipes'),
    path('<str:mongodb_id>',                 views.recipes_mongodb_id,               name='recipes_mongodb_id'),
    path('<str:mongodb_id>/',                views.recipes_mongodb_id,               name='recipes_mongodb_id_slash'),
    #path('builder',                         views.recipes_builder,                  name='recipes_builder'),
    #path('builder/',                        views.recipes_builder,                  name='recipes_builder'),
    #path('builder/new',                     views.recipes_builder_new,              name='recipes_builder_new'),
    #path('builder/new/',                    views.recipes_builder_new,              name='recipes_builder_new_slash'),
    #path('builder/<int:recipe_id>',         views.recipes_builder_recipe_id,        name='recipes_builder_recipe_id'),
    #path('builder/<int:recipe_id>/',        views.recipes_builder_recipe_id,        name='recipes_builder_recipe_id_slash'),
    #path('builder/<int:recipe_id>/add',     views.recipes_builder_recipe_id_add,    name='recipes_builder_recipe_id_add'),
    #path('builder/<int:recipe_id>/add/',    views.recipes_builder_recipe_id_add,    name='recipes_builder_recipe_id_add_slash'),
    #path('builder/<int:recipe_id>/finish',  views.recipes_builder_recipe_id_finish, name='recipes_builder_recipe_id_finish'),
    #path('builder/<int:recipe_id>/finish/', views.recipes_builder_recipe_id_finish, name='recipes_builder_recipe_id_finish_slash'),
]
