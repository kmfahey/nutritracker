#!/usr/bin/python

import math

from decouple import config

from operator import and_, attrgetter

from functools import reduce

from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.db.models import Q

from .models import Food, Recipe
from utils import Recipe_Detailed, Navigation_Links_Displayer, generate_pagination_links, get_cgi_params, slice_output_list_by_page, cast_to_int, Fdc_Api_Contacter


navigation_link_displayer = Navigation_Links_Displayer({'/recipes/': "Main Recipes List"})

default_page_size = config("DEFAULT_PAGE_SIZE")


@require_http_methods(["GET"])
def recipes(request):
    # This code is copy/pasted from foods.views.foods, ugh. Not sure how to generalize it though.
    recipes_template = loader.get_template('recipes/recipes.html')
    cgi_params = get_cgi_params(request)
    context = {'more_than_one_page': False, 'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/recipes/")}

    retval = cast_to_int(cgi_params.get("page_size", default_page_size), 'page_size', recipes_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval
    retval = cast_to_int(cgi_params.get("page_number", 1), 'page_number', recipes_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_number = retval

    recipe_objs = [Recipe_Detailed.from_json_obj(recipe_model_obj.serialize()) for recipe_model_obj in Recipe.objects.filter()]
    recipe_objs.sort(key=attrgetter('recipe_name'))
    number_of_results = len(recipe_objs)
    number_of_pages = math.ceil(number_of_results / page_size)
    if page_number > number_of_pages:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        context["pagination_links"] = generate_pagination_links("/recipes/", number_of_results, page_size, page_number)
        return HttpResponse(recipes_template.render(context, request))

    if len(recipe_objs) > page_size:
        recipe_objs = slice_output_list_by_page(recipe_objs, page_size, page_number)
        context["more_than_one_page"] = True
        context["pagination_links"] = generate_pagination_links("/recipes/", number_of_results, page_size, page_number)
    context['recipe_objs'] = recipe_objs

    return HttpResponse(recipes_template.render(context, request))
