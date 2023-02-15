#!/usr/bin/python3

from django.urls import path

from . import views


urlpatterns = [
    path('',                                views.users,                        name='users'),
#    path('new',                            views.users_new,                    name='users_new'),
#    path('new/',                           views.users_new,                    name='users_new_slash'),
#    path('<str:user_id>/password',         views.users_user_id_password,       name='users_user_id_password'),
#    path('<str:user_id>/password/',        views.users_user_id_password,       name='users_user_id_password_slash'),
#    path('<str:user_id>',                  views.users_user_id,                name='users_user_id'),
#    path('<str:user_id>/',                 views.users_user_id,                name='users_user_id_slash'),
#    path('<str:user_id>/edit_profile',     views.users_user_id_edit_profile,   name='users_user_id_edit_profile'),
#    path('<str:user_id>/edit_profile/',    views.users_user_id_edit_profile,   name='users_user_id_edit_profile_slash'),
#    path('<str:user_id>/confirm_delete',   views.users_user_id_confirm_delete, name='users_user_id_confirm_delete'),
#    path('<str:user_id>/confirm_delete/',  views.users_user_id_confirm_delete, name='users_user_id_confirm_delete_slash'),
#    path('delete',                         views.users_delete,                 name='users_delete'),
#    path('delete/',                        views.users_delete,                 name='users_delete_slash')
]
