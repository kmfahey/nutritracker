#!/usr/bin/python

import math
import bcrypt
import html
import urllib.parse

from bson.objectid import ObjectId, InvalidId

from decouple import config

from operator import and_, attrgetter

from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template import loader

from django.contrib.auth.models import User
from .models import Account

from utils import ACTIVITY_LEVELS_TABLE, FEET_TO_METERS_CONVERSION_FACTOR, POUNDS_TO_KILOGRAMS_CONVERSION_FACTOR, \
        BMI_THRESHOLDS, Navigation_Links_Displayer, get_cgi_params, cast_to_int, cast_to_float, check_str_param


URL_RESERVED_WORDS = ('new_user', 'delete_user', 'auth')

navigation_link_displayer = Navigation_Links_Displayer({'/users/': 'Login'})


def _collect_account_params_from_cgi(cgi_params, template, context, request):
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


def _retrieve_user_and_account_objs(request, username, template, context):
    if request.user.username != username:
        context['error'] = True
        context['message'] = f"You are not the user with username='{username}', you may not access this page."
        return HttpResponse(template.render(context, request), status=404)
    elif not request.user.is_authenticated:
        context['error'] = True
        context['message'] = f'To access your profile page, please <a href="/users/">login</a>.'
        return HttpResponse(template.render(context, request), status=404)

    user_model_obj = request.user

    try:
        account_model_obj = Account.objects.get(username=username)
    except Account.DoesNotExist:
        context['error'] = True
        context['message'] = f"No account with username='{username}'"
        return HttpResponse(template.render(context, request), status=500)

    return user_model_obj, account_model_obj


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

    user_model_obj = authenticate(username=username, password=cgi_params['password'])

    if user_model_obj is None:
        context['error'] = True
        context['message'] = f"Password submitted does not match password on record"
        return HttpResponse(users_template.render(context, request))

    login(request, user_model_obj)

    return redirect(f"/users/{username}/")


@require_http_methods(["GET", "POST"])
def users_username(request, username):
    users_username_template = loader.get_template('users/users_+username+.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"), 'error': False, 'message': ''}
    cgi_params = get_cgi_params(request)

    retval = _retrieve_user_and_account_objs(request, username, users_username_template, context)
    if isinstance(retval, HttpResponse):
        return retval
    _, account_model_obj = retval
    context["user_model_obj"], context["account_model_obj"] = retval

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

    retval = _retrieve_user_and_account_objs(request, username, users_username_edit_profile_template, context)
    if isinstance(retval, HttpResponse):
        return retval
    _, account_model_obj = retval
    context["user_model_obj"], context["account_model_obj"] = retval

    if len(cgi_params):
        retval = _collect_account_params_from_cgi(cgi_params, users_username_edit_profile_template, context, request)
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
        retval = _collect_account_params_from_cgi(cgi_params, users_new_user_template, context, request)
        if isinstance(retval, HttpResponse):
            return retval
        account_obj_init_dict = retval
        account_obj_init_dict['height'] = account_obj_init_dict['height_feet'] + account_obj_init_dict['height_inches'] / 12
        del account_obj_init_dict['height_feet'], account_obj_init_dict['height_inches']

        user_obj_init_dict = dict()
        for param_name in ('username', 'password_initial', 'password_confirm'):
            retval = check_str_param(cgi_params.get(param_name, None), param_name, users_new_user_template, context, request, upperb=32)
            if isinstance(retval, HttpResponse):
                return retval
            user_obj_init_dict[param_name] = retval

        if user_obj_init_dict['username'] in URL_RESERVED_WORDS:
            quoted_reserved_words = tuple(map(lambda strval: "'%s'" % strval, URL_RESERVED_WORDS))
            reserved_words_expr = "%s, or %s" % (", ".join(quoted_reserved_words[:-1]), quoted_reserved_words[-1])
            context['error'] = True
            context['message'] = f"Username must not be one of {quoted_reserved_words}"
            return HttpResponse(users_new_user_template.render(context, request))
        account_obj_init_dict['username'] = user_obj_init_dict['username']

        if user_obj_init_dict['password_initial'] != user_obj_init_dict['password_confirm']:
            context['error'] = True
            context['message'] = f"Passwords do not match"
            return HttpResponse(users_new_user_template.render(context, request))

        user_model_obj = User.objects.create_user(username=user_obj_init_dict["username"], password=user_obj_init_dict["password_initial"])
        user_model_obj.save()

        user_model_obj = authenticate(username=user_obj_init_dict["username"], password=user_obj_init_dict["password_initial"])

        if user_model_obj is None:
            context['error'] = True
            context['message'] = f"Could not authenticate user object with known-good password"
            return HttpResponse(users_template.render(context, request), status=500)

        login(request, user_model_obj)

        account_model_obj = Account(**account_obj_init_dict)
        account_model_obj.save()

        redir_cgi_params = urllib.parse.urlencode({'error': False, 'message': 'Your profile details have been set, and your account is ready to use.'})
        return redirect(f"/users/{user_model_obj.username}/?{redir_cgi_params}")
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

    retval = _retrieve_user_and_account_objs(request, username, users_username_change_password_template, context)
    if isinstance(retval, HttpResponse):
        return retval
    user_model_obj, account_model_obj = retval

    if (len(cgi_params) and 'current_password' in cgi_params and 'new_password_initial' in cgi_params
            and 'new_password_confirm' in cgi_params):

        password_params = dict()
        for param_name in ('current_password', 'new_password_initial', 'new_password_confirm'):
            retval = check_str_param(cgi_params.get(param_name, None), param_name, users_username_change_password_template, context, request, upperb=32)
            if isinstance(retval, HttpResponse):
                return retval
            password_params[param_name] = retval

        user_model_obj = authenticate(username=username, password=password_params["current_password"])

        if user_model_obj is None:
            context['error'] = True
            context['message'] = f"Current password submitted does not match password on record"
            return HttpResponse(users_username_change_password_template.render(context, request))
        elif password_params['new_password_initial'] != password_params['new_password_confirm']:
            context['error'] = True
            context['message'] = f"Passwords do not match"
            return HttpResponse(users_username_change_password_template.render(context, request))

        user_model_obj.set_password(password_params['new_password_initial'])
        user_model_obj.save()

        # I don't actually know whether the session created by login() would
        # stop working if the password used to authenticate for it was changed,
        # but that's my expectation, so I'm re-authenticating with the password
        # just set.
        user_model_obj = authenticate(username=username, password=password_params['new_password_initial'])

        if user_model_obj is None:
            context['error'] = True
            context['message'] = f"Could not authenticate user object with known-good password"
            return HttpResponse(users_template.render(context, request), status=500)

        login(request, user_model_obj)

        context['error'] = False
        context['message'] = f"Your password has been updated."

    return HttpResponse(users_username_change_password_template.render(context, request))


@require_http_methods(["GET"])
def users_username_confirm_delete_user(request, username):
    users_username_confirm_delete_user_template = loader.get_template('users/users_+username+_confirm_delete_user.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"),
               'error': False, 'message': '', 'username': username}
    cgi_params = get_cgi_params(request)

    retval = _retrieve_user_and_account_objs(request, username, users_username_confirm_delete_user_template, context)
    if isinstance(retval, HttpResponse):
        return retval
    user_model_obj, account_model_obj = retval

    context['message'] = "Are you sure you want to delete your account?"

    return HttpResponse(users_username_confirm_delete_user_template.render(context, request))


@require_http_methods(["GET", "POST"])
def users_delete_user(request):
    users_delete_user_template = loader.get_template('users/users_delete_user.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"),
               'error': False, 'message': ''}
    cgi_params = get_cgi_params(request)

    if not len(cgi_params) or 'username' not in cgi_params:
        context['error'] = True
        context['message'] = f"No 'username' CGI parameter specified, unable to delete user"
        return HttpResponse(users_delete_user_template.render(context, request))

    username = check_str_param(cgi_params.get('username', None), 'username', users_delete_user_template, context, request)

    retval = _retrieve_user_and_account_objs(request, username, users_delete_user_template, context)
    if isinstance(retval, HttpResponse):
        return retval
    user_model_obj, account_model_obj = retval

    user_model_obj.delete()
    account_model_obj.delete()

    context['message'] = f"User account with username='{username}' deleted"

    return HttpResponse(users_delete_user_template.render(context, request))

