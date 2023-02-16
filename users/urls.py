#!/usr/bin/python3

from django.urls import path

from . import views


urlpatterns = [
    path('',                                views.users,                         name='users'),
    path('auth',                            views.users_auth,                    name='users_auth'),
    path('auth/',                           views.users_auth,                    name='users_auth_slash'),
    path('<str:username>',                  views.users_username,                name='users_username'),
    path('<str:username>/',                 views.users_username,                name='users_username_slash'),
#    path('new',                             views.users_new,                     name='users_new'),
#    path('new/',                            views.users_new,                     name='users_new_slash'),
#    path('<str:username>/password',         views.users_username_password,       name='users_username_password'),
#    path('<str:username>/password/',        views.users_username_password,       name='users_username_password_slash'),
#    path('<str:username>/edit_profile',     views.users_username_edit_profile,   name='users_username_edit_profile'),
#    path('<str:username>/edit_profile/',    views.users_username_edit_profile,   name='users_username_edit_profile_slash'),
#    path('<str:username>/confirm_delete',   views.users_username_confirm_delete, name='users_username_confirm_delete'),
#    path('<str:username>/confirm_delete/',  views.users_username_confirm_delete, name='users_username_confirm_delete_slash'),
#    path('delete',                          views.users_delete,                  name='users_delete'),
#    path('delete/',                         views.users_delete,                  name='users_delete_slash')
]
