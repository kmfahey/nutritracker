#!/usr/bin/python3

from django.urls import path

from . import views


urlpatterns = [
    path('',                                   views.users,                              name='users'),
    path('auth',                               views.users_auth,                         name='users_auth'),
    path('auth/',                              views.users_auth,                         name='users_auth_slash'),
    path('new_user',                           views.users_new_user,                     name='users_new_user'),
    path('new_user/',                          views.users_new_user,                     name='users_new_user_slash'),
    path('delete_user',                        views.users_delete_user,                  name='users_delete_user'),
    path('delete_user/',                       views.users_delete_user,                  name='users_delete_user_slash'),
    path('<str:username>',                     views.users_username,                     name='users_username'),
    path('<str:username>/',                    views.users_username,                     name='users_username_slash'),
    path('<str:username>/edit_profile',        views.users_username_edit_profile,        name='users_username_edit_profile'),
    path('<str:username>/edit_profile/',       views.users_username_edit_profile,        name='users_username_edit_profile_slash'),
    path('<str:username>/change_password',     views.users_username_change_password,     name='users_username_change_password'),
    path('<str:username>/change_password/',    views.users_username_change_password,     name='users_username_change_password_slash'),
    path('<str:username>/confirm_delete_user',  views.users_username_confirm_delete_user, name='users_username_confirm_delete_user'),
    path('<str:username>/confirm_delete_user/', views.users_username_confirm_delete_user, name='users_username_confirm_delete_user_slash')
]
