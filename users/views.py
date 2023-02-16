#!/usr/bin/python

import math
import bcrypt

from django.shortcuts import render

from bson.objectid import ObjectId, InvalidId

from decouple import config

from operator import and_, attrgetter

from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template import loader

from .models import Account

from utils import ACTIVITY_LEVELS_TABLE, FEET_TO_METERS_CONVERSION_FACTOR, POUNDS_TO_KILOGRAMS_CONVERSION_FACTOR, BMI_THRESHOLDS, Navigation_Links_Displayer,  get_cgi_params


navigation_link_displayer = Navigation_Links_Displayer({'/users/': 'Login'})


@require_http_methods(["GET"])
def users(request):
    users_template = loader.get_template('users/users.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"), 'error': False, 'message': ''}
    return HttpResponse(users_template.render(context, request))


@require_http_methods(["POST"])
def users_auth(request):
    cgi_params = get_cgi_params(request)
    users_template = loader.get_template('users/users.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"), 'error': False, 'message': ''}

    if not len(cgi_params.keys()) or 'username' not in cgi_params or 'password' not in cgi_params:
        return redirect(originating_url)
    username = cgi_params['username']

    if not (0 < len(username) <= 32):
        context['error'] = True
        context['message'] = "Username must be more than 0 characters long, and at most 32 characters long"
        return HttpResponse(users_template.render(context, request), status=422)
    try:
        account_model_obj = Account.objects.get(username=username)
    except Account.DoesNotExist:
        context['error'] = True
        context['message'] = f"No user account with username='{username}'"
        return HttpResponse(users_template.render(context, request), status=422)
    submitted_password = cgi_params['password'].encode('utf-8')
    authenticates = bcrypt.checkpw(submitted_password, account_model_obj.password_encrypted)
    if not authenticates:
        context['error'] = True
        context['message'] = f"Password submitted does not match password on record"
        return HttpResponse(users_template.render(context, request), status=422)

    return redirect(f"/users/{username}/")


def users_username(request, username):
    users_username_template = loader.get_template('users/users_+username+.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"), 'error': False, 'message': ''}

    try:
        account_model_obj = Account.objects.get(username=username)
    except Account.DoesNotExist:
        context['error'] = True
        context['message'] = f"No user account with username='{username}'"
        return HttpResponse(users_username_template.render(context, request), status=404)
    context["account_model_obj"] = account_model_obj

    context["height_feet"] = math.floor(account_model_obj.height)
    context["height_inches"] = round((account_model_obj.height % 1) * 12, 1)
    context["weight"] = round(account_model_obj.weight, 1)
    context["activity_level"] = ACTIVITY_LEVELS_TABLE[account_model_obj.activity_level]
    context["weight_goal"] = f"{account_model_obj.weight_goal} lb / week" if account_model_obj.weight_goal != 0 else "maintain current weight"

    height_in_meters = account_model_obj.height * FEET_TO_METERS_CONVERSION_FACTOR
    weight_in_kilograms = account_model_obj.weight * POUNDS_TO_KILOGRAMS_CONVERSION_FACTOR
    context["body_mass_index"] = body_mass_index = round(weight_in_kilograms / (height_in_meters)**2, 1)
    for lower_bound, upper_bound, reading in BMI_THRESHOLDS:
        if lower_bound <= body_mass_index <= upper_bound:
            context["bmi_reading"] = reading

    height_in_centimeters = height_in_meters * 100
    if account_model_obj.gender_at_birth == "M":
        basal_metabolic_rate = 66.473 + (13.7516 * weight_in_kilograms) + (5.0033 * height_in_centimeters) - (6.755 * account_model_obj.age)
    else:
        basal_metabolic_rate = 655.0955 + (9.5634 * weight_in_kilograms) + (1.8496 * height_in_centimeters) - (4.6756 * account_model_obj.age)

    match account_model_obj.activity_level:
        case 1:
            context["active_metabolic_rate"] = round(basal_metabolic_rate * 1.2)
        case 2:
            context["active_metabolic_rate"] = round(basal_metabolic_rate * 1.375)
        case 3:
            context["active_metabolic_rate"] = round(basal_metabolic_rate * 1.55)
        case 4:
            context["active_metabolic_rate"] = round(basal_metabolic_rate * 1.725)
        case 5:
            context["active_metabolic_rate"] = round(basal_metabolic_rate * 1.9)

    return HttpResponse(users_username_template.render(context, request))


#def users_new(request):
#    pass
#
#def users_username_password(request, username):
#    pass
#
#def users_username_edit_profile(request, username):
#    pass
#
#def users_username_confirm_delete(request, username):
#    pass
#
#def users_delete(request):
#    pass
