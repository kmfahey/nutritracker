#!/usr/bin/python

import math

from bson.objectid import ObjectId

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



# Much of this is adapted from foods.views.foods with just symbols changed,
# which is Not a Good Look. In the past I've generalized such code into
# higher-order functions and used a closure in each case of duplicated code. The
# downside is the code inside the higher-order function is created with a lot of
# find-and-replace and it becomes unreadable, and a pain to maintain. Not sure
# it's worth it this time.


@require_http_methods(["GET"])
def recipes(request):
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

@require_http_methods(["GET"])
def recipes_mongodb_id(request, mongodb_id):
    template = loader.get_template('recipes/recipes_+mongodb_id+.html')
    try:
        recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
    except Recipe.DoesNotExist:
        return HttpResponse(f"no object in 'recipes' collection in 'nutritracker' data store with _id='{mongodb_id}'", status=404)
    recipe_obj = Recipe_Detailed.from_json_obj(recipe_model_obj.serialize())
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/recipes/")}
    context['recipe_obj'] = context['food_or_recipe_obj'] = recipe_obj
    return HttpResponse(template.render(context, request))


