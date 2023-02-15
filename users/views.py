#!/usr/bin/python

import math

from django.shortcuts import render

from bson.objectid import ObjectId, InvalidId

from decouple import config

from operator import and_, attrgetter

from functools import reduce

from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template import loader

from utils import Nutrient, Recipe_Detailed, Ingredient_Detailed, Food_Detailed, Navigation_Links_Displayer, \
        generate_pagination_links, slice_output_list_by_page, retrieve_pagination_params, get_cgi_params, cast_to_int


navigation_link_displayer = Navigation_Links_Displayer({'/users/': 'Login'})


@require_http_methods(["GET"])
def users(request):
    recipes_template = loader.get_template('users/users.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/users/"), 'error': False, 'message': ''}
    return HttpResponse(recipes_template.render(context, request))


#def users_new(request):
#    pass
#
#def users_user_id_password(request, user_id):
#    pass
#
#def users_user_id(request, user_id):
#    pass
#
#def users_user_id_edit_profile(request, user_id):
#    pass
#
#def users_user_id_confirm_delete(request, user_id):
#    pass
#
#def users_delete(request):
#    pass
