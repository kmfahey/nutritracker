#!/usr/bin/python

import math
import bcrypt
import html
import urllib.parse

from django.shortcuts import render

from bson.objectid import ObjectId, InvalidId

from decouple import config

from operator import and_, attrgetter

from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template import loader

from .models import Account

from utils import ACTIVITY_LEVELS_TABLE, FEET_TO_METERS_CONVERSION_FACTOR, POUNDS_TO_KILOGRAMS_CONVERSION_FACTOR, \
        BMI_THRESHOLDS, Navigation_Links_Displayer, get_cgi_params, cast_to_int, cast_to_float, check_str_param


URL_RESERVED_WORDS = ('new_user', 'delete_user', 'auth')

navigation_link_displayer = Navigation_Links_Displayer({'/users/': 'Login'})


def _collect_user_params_from_cgi(cgi_params, template, context, request):
    return_dict = dict()

    for param_name in ('display_name', 'gender_at_birth', 'gender_identity', 'pronouns'):
        retval = check_str_param(cgi_params.get(param_name, None), param_name, template, context, request)
        if isinstance(retval, HttpResponse):
            return retval
        return_dict[param_name] = retval

    for param_name, lowerb, upperb in (('age', 13, 120),        ('activity_level', 1, 5),
                                       ('weight_goal', -2, 2),  ('height_feet', 4, 8)):
        retval = cast_to_int(cgi_params.get(param_name, None), param_name, template, context, request, lowerb=lowerb, upperb=upperb)
        if isinstance(retval, HttpResponse):
            return retval
        return_dict[param_name] = retval

    retval = cast_to_float(cgi_params.get('height_inches', None), 'height_inches', template, context, request, lowerb=0, upperb=11.999)
    if isinstance(retval, HttpResponse):
        return retval
    return_dict['height_inches'] = retval

    retval = cast_to_float(cgi_params.get('weight', None), 'weight', template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    return_dict['weight'] = retval

    return return_dict


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
        return HttpResponse(users_template.render(context, request))
    try:
        account_model_obj = Account.objects.get(username=username)
    except Account.DoesNotExist:
        context['error'] = True
        context['message'] = f"No user account with username='{username}'"
        return HttpResponse(users_template.render(context, request))
    submitted_password = cgi_params['password'].encode('utf-8')
    authenticates = bcrypt.checkpw(submitted_password, account_model_obj.password_encrypted)
    if not authenticates:
        context['error'] = True
        context['message'] = f"Password submitted does not match password on record"
        return HttpResponse(users_template.render(context, request))

    return redirect(f"/users/{username}/")


@require_http_methods(["GET", "POST"])
def users_username(request, username):
    users_username_template = loader.get_template('users/users_+username+.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"), 'error': False, 'message': ''}
    cgi_params = get_cgi_params(request)

    try:
        account_model_obj = Account.objects.get(username=username)
    except Account.DoesNotExist:
        context['error'] = True
        context['message'] = f"No user account with username='{username}'"
        return HttpResponse(users_username_template.render(context, request), status=404)
    context["account_model_obj"] = account_model_obj

    if cgi_params and 'message' in cgi_params and 'error' in cgi_params:
        context['error'] = False if cgi_params.get('error', None) == 'False' else True
        # Since message is a CGI-submitted value that is displayed on a webpage,
        # it's necessary to sanitize the input. I've opted to escape all HTML
        # metacharacters using html.escape().
        context["message"] = html.escape(cgi_params.get("message", ""))

    context["gender_at_birth"] = "male" if account_model_obj.gender_at_birth == "M" else "female"
    context["pronouns"] = ("he/him" if account_model_obj.pronouns == "he"
                           else "she/her" if account_model_obj.pronouns == "she"
                           else "they/them")

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


@require_http_methods(["GET", "POST"])
def users_username_edit_profile(request, username):
    profile_url = f"/users/{username}/"
    users_username_edit_profile_template = loader.get_template('users/users_+username+_edit_profile.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"), 'error': False, 'message': ''}
    cgi_params = get_cgi_params(request)

    try:
        account_model_obj = Account.objects.get(username=username)
    except Account.DoesNotExist:
        context['error'] = True
        context['message'] = f"No user account with username='{username}'"
        return HttpResponse(users_username_edit_profile_template.render(context, request), status=404)
    context["account_model_obj"] = account_model_obj

    if len(cgi_params):
        retval = _collect_user_params_from_cgi(cgi_params, users_username_edit_profile_template, context, request)
        if isinstance(retval, HttpResponse):
            return retval
        account_obj_update_dict = retval

        for attr_name, attr_val in account_obj_update_dict.items():
            setattr(account_model_obj, attr_name, attr_val)

        account_model_obj.save()

        redir_cgi_params = urllib.parse.urlencode({'error': False, 'message': 'Your profile details have been updated.'})
        return redirect(f"{profile_url}?{redir_cgi_params}")
    else:
        context["username"] = username
        context["display_name"] = account_model_obj.display_name

        context["selected_if_male"] =      "selected" if account_model_obj.gender_at_birth == "M" else ""
        context["selected_if_female"] =    "selected" if account_model_obj.gender_at_birth == "F" else ""

        context["gender_identity"] = account_model_obj.gender_identity

        context["selected_if_he_him"] =    "selected" if account_model_obj.pronouns == "he" else ""
        context["selected_if_she_her"] =   "selected" if account_model_obj.pronouns == "she" else ""
        context["selected_if_they_them"] = "selected" if account_model_obj.pronouns == "they" else ""

        context["age"] = account_model_obj.age

        context["height_feet"] = math.floor(account_model_obj.height)
        context["height_inches"] = round((account_model_obj.height % 1) * 12, 1)
        context["weight"] = round(account_model_obj.weight, 1)

        context["selected_if_activity_level_1"] = "selected" if account_model_obj.activity_level == 1 else ""
        context["selected_if_activity_level_2"] = "selected" if account_model_obj.activity_level == 2 else ""
        context["selected_if_activity_level_3"] = "selected" if account_model_obj.activity_level == 3 else ""
        context["selected_if_activity_level_4"] = "selected" if account_model_obj.activity_level == 4 else ""
        context["selected_if_activity_level_5"] = "selected" if account_model_obj.activity_level == 5 else ""

        context["selected_if_weight_goal_plus_2"] = "selected"   if account_model_obj.weight_goal == 2 else ""
        context["selected_if_weight_goal_plus_1"] = "selected"   if account_model_obj.weight_goal == 1 else ""
        context["selected_if_weight_goal_maintain"] = "selected" if account_model_obj.weight_goal == 0 else ""
        context["selected_if_weight_goal_minus_1"] = "selected"  if account_model_obj.weight_goal == -1 else ""
        context["selected_if_weight_goal_minus_2"] = "selected"  if account_model_obj.weight_goal == -2 else ""

        return HttpResponse(users_username_edit_profile_template.render(context, request))


@require_http_methods(["GET", "POST"])
def users_new_user(request):
    users_new_user_template = loader.get_template('users/users_new_user.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"), 'error': False, 'message': ''}
    cgi_params = get_cgi_params(request)

    if len(cgi_params):
        retval = _collect_user_params_from_cgi(cgi_params, users_new_user_template, context, request)
        if isinstance(retval, HttpResponse):
            return retval
        account_obj_init_dict = retval
        account_obj_init_dict['height'] = account_obj_init_dict['height_feet'] + account_obj_init_dict['height_inches'] / 12
        del account_obj_init_dict['height_feet'], account_obj_init_dict['height_inches']

        account_other_params = dict()
        for param_name in ('username', 'password_initial', 'password_confirm'):
            retval = check_str_param(cgi_params.get(param_name, None), param_name, users_new_user_template, context, request, upperb=32)
            if isinstance(retval, HttpResponse):
                return retval
            account_other_params[param_name] = retval

        if account_other_params['username'] in URL_RESERVED_WORDS:
            quoted_reserved_words = tuple(map(lambda strval: "'%s'" % strval, URL_RESERVED_WORDS))
            reserved_words_expr = "%s, or %s" % (", ".join(quoted_reserved_words[:-1]), quoted_reserved_words[-1])
            context['error'] = True
            context['message'] = f"Username must not be one of {quoted_reserved_words}"
            return HttpResponse(users_new_user_template.render(context, request))
        account_obj_init_dict['username'] = account_other_params['username']

        if account_other_params['password_initial'] != account_other_params['password_confirm']:
            context['error'] = True
            context['message'] = f"Passwords do not match"
            return HttpResponse(users_new_user_template.render(context, request))
        password_bytes = account_other_params['password_initial'].encode('utf-8')
        salt = bcrypt.gensalt()
        account_obj_init_dict['password_encrypted'] = bcrypt.hashpw(password_bytes, salt)

        account_model_obj = Account(**account_obj_init_dict)
        account_model_obj.save()

        redir_cgi_params = urllib.parse.urlencode({'error': False, 'message': 'Your profile details have been set, and your account is ready to use.'})
        return redirect(f"/users/{account_model_obj.username}/?{redir_cgi_params}")
    else:
        context["username"] = ""
        context["display_name"] = ""
        context["selected_if_male"] = "selected"
        context["gender_identity"] = ""
        context["selected_if_he_him"] = "selected"
        context["age"] = ""
        context["height_feet"] = ""
        context["height_inches"] = ""
        context["weight"] = ""
        context["selected_if_activity_level_3"] = "selected"
        context["selected_if_weight_goal_maintain"] = "selected"

        return HttpResponse(users_new_user_template.render(context, request))


@require_http_methods(["GET", "POST"])
def users_username_change_password(request, username):
    users_username_change_password_template = loader.get_template('users/users_+username+_change_password.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"),
               'error': False, 'message': '', 'username': username}
    cgi_params = get_cgi_params(request)

    try:
        account_model_obj = Account.objects.get(username=username)
    except Account.DoesNotExist:
        context['error'] = True
        context['message'] = f"No user account with username='{username}'"
        return HttpResponse(users_username_change_password_template.render(context, request), status=404)

    if (len(cgi_params) and 'current_password' in cgi_params and 'new_password_initial' in cgi_params
            and 'new_password_confirm' in cgi_params):

        password_params = dict()
        for param_name in ('current_password', 'new_password_initial', 'new_password_confirm'):
            retval = check_str_param(cgi_params.get(param_name, None), param_name, users_username_change_password_template, context, request, upperb=32)
            if isinstance(retval, HttpResponse):
                return retval
            password_params[param_name] = retval

        submitted_password = password_params['current_password'].encode('utf-8')
        authenticates = bcrypt.checkpw(submitted_password, account_model_obj.password_encrypted)

        if not authenticates:
            context['error'] = True
            context['message'] = f"Current password submitted does not match password on record"
            return HttpResponse(users_username_change_password_template.render(context, request))
        elif password_params['new_password_initial'] != password_params['new_password_confirm']:
            context['error'] = True
            context['message'] = f"Passwords do not match"
            return HttpResponse(users_username_change_password_template.render(context, request))

        password_bytes = password_params['new_password_initial'].encode('utf-8')
        salt = bcrypt.gensalt()
        account_model_obj.password_encrypted = bcrypt.hashpw(password_bytes, salt)

        account_model_obj.save()
        context['error'] = False
        context['message'] = f"Your password has been updated."

    return HttpResponse(users_username_change_password_template.render(context, request))




#def users_username_confirm_delete(request, username):
#    pass
#
#def users_delete(request):
#    pass
