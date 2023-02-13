#!/usr/bin/python

import math

from bson.objectid import ObjectId

from decouple import config

from operator import and_, attrgetter

from functools import reduce

from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template import loader
from django.db.models import Q

from .models import Food, Recipe
from utils import Recipe_Detailed, Food_Detailed, Navigation_Links_Displayer, generate_pagination_links, slice_output_list_by_page, retrieve_pagination_params


navigation_link_displayer = Navigation_Links_Displayer({'/recipes/': "Main Recipes List", '/recipes/search/': "Recipes Search"})

default_page_size = config("DEFAULT_PAGE_SIZE")


# Much of this is adapted from foods.views.foods with just symbols changed,
# which is Not a Good Look. In the past I've generalized such code into
# higher-order functions and used a closure in each case of duplicated code. The
# downside is the code inside each higher-order function is created with a lot
# of find-and-replace and it becomes unreadable & unmaintainable. Not sure I
# want to go down the same path. When it's Don't Repeat Yourself vs. readable &
# maintainable code, I think the latter wins.


@require_http_methods(["GET"])
def recipes(request):
    recipes_template = loader.get_template('recipes/recipes.html')
    context = {'more_than_one_page': False, 'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/recipes/")}

    retval = retrieve_pagination_params(recipes_template, context, request, default_page_size, query=False)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval["page_size"]
    page_number = retval["page_number"]

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


@require_http_methods(["GET"])
def search(request):
    template = loader.get_template('recipes/recipes_search.html')
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/recipes/search/")
    context = {'subordinate_navigation': subordinate_navigation, 'message': '', 'more_than_one_page': False}
    return HttpResponse(template.render(context, request))


@require_http_methods(["GET", "POST"])
def search_results(request):
    search_url = "/recipes/search/"
    subordinate_navigation = navigation_link_displayer.full_href_list_callable()
    context = {'subordinate_navigation': subordinate_navigation, 'message': '', 'more_than_one_page': False}
    search_template = loader.get_template('recipes/recipes_search.html')
    search_results_template = loader.get_template('recipes/recipes_search_results.html')

    retval = retrieve_pagination_params(search_template, context, request, default_page_size, search_url, query=True)
    if isinstance(retval, HttpResponse):
        return retval
    search_query = retval["search_query"]
    page_size = retval["page_size"]
    page_number = retval["page_number"]
    kws = search_query.strip().split()

    # This is equivelant to q_term = (Q(recipe_name__icontains=kws[0]) & Q(recipe_name__icontains=kws[1]) & ... & Q(recipe_name__icontains=kws[-1]))
    q_term = reduce(and_, (Q(recipe_name__icontains=kw) for kw in kws))
    recipe_objs = list(Recipe.objects.filter(q_term))
    recipe_objs.sort(key=attrgetter('recipe_name'))
    if not len(recipe_objs):
        context["message"] = "No matches"
        return HttpResponse(search_template.render(context, request))
    elif len(recipe_objs) <= page_size and page_number > 1:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        context["pagination_links"] = generate_pagination_links("/recipes/search_results/", len(recipe_objs), page_size, page_number, search_query=search_query)
        return HttpResponse(search_template.render(context, request))

    recipe_objs = [Recipe_Detailed.from_model_obj(recipe_model_obj) for recipe_model_obj in recipe_objs]
    if len(recipe_objs) > page_size:
        context["more_than_one_page"] = True
        context["pagination_links"] = generate_pagination_links("/recipes/search_results/", len(recipe_objs), page_size, page_number, search_query=search_query)
        context['recipe_objs'] = slice_output_list_by_page(recipe_objs, page_size, page_number)
    else:
        context["more_than_one_page"] = False
        context['recipe_objs'] = recipe_objs
    return HttpResponse(search_results_template.render(context, request))
