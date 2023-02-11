#!/usr/bin/python

import math

from decouple import config

from operator import and_, attrgetter

from functools import reduce

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.db.models import Q

from .models import Food
from utils import Food_Detailed, Navigation_Links_Displayer, generate_pagination_links, get_cgi_params, slice_output_list_by_page, cast_int


navigation_link_displayer = Navigation_Links_Displayer({'/foods/': "Main Foods List", "/foods/local_search/": "Local Food Search"})

PAGE_SIZE = config("DEFAULT_PAGE_SIZE")


def index(request):
    foods_template = loader.get_template('foods.html')
    cgi_params = get_cgi_params(request)
    context = {'more_than_one_page': False}

    retval = cast_int(cgi_params.get("page_size", PAGE_SIZE), 'page_size', foods_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval
    retval = cast_int(cgi_params.get("page", 1), 'page', foods_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    current_page = retval

    food_objs = [Food_Detailed.from_model_object(food_model_obj) for food_model_obj in Food.objects.filter()]
    food_objs.sort(key=attrgetter('food_name'))
    number_of_results = len(food_objs)
    number_of_pages = math.ceil(number_of_results / page_size)
    if current_page > number_of_pages:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        context["pagination_links"] = generate_pagination_links("/foods/", number_of_results, page_size, current_page)
        return HttpResponse(foods_template.render(context, request))

    if len(food_objs) > page_size:
        food_objs = slice_output_list_by_page(food_objs, page_size, current_page)
        context["more_than_one_page"] = True
        context["pagination_links"] = generate_pagination_links("/foods/", number_of_results, page_size, current_page)
    context['subordinate_navigation'] = navigation_link_displayer.href_list_wo_one_callable("/foods/")
    context['food_objs'] = food_objs

    return HttpResponse(foods_template.render(context, request))

def display_food(request, fdc_id):
    template = loader.get_template('foods_+fdc_id+.html')
    food_model_objs = Food.objects.filter(fdc_id=fdc_id)
    if not len(food_model_objs):
        return HttpResponse(f"no object in 'foods' collection in 'nutritracker' data store with FDC ID {fdc_id}", status=404)
    elif len(food_model_objs) > 1:
        return HttpResponse(f"inconsistent state: multiple objects matching query for FDC ID {fdc_id}", status=500)
    food_model_obj = food_model_objs[0]
    food_obj = Food_Detailed.from_model_object(food_model_obj)
    subordinate_navigation = navigation_link_displayer.full_href_list_callable()
    context = {'food_obj':food_obj, 'subordinate_navigation': subordinate_navigation}
    return HttpResponse(template.render(context, request))

def local_search(request):
    template = loader.get_template('foods_local_search.html')
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/foods/local_search/")
    context = {'subordinate_navigation': subordinate_navigation, 'message':'', 'more_than_one_page':False}
    return HttpResponse(template.render(context, request))

def local_search_results(request):
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/foods/local_search/")
    context = {'subordinate_navigation': subordinate_navigation, 'message': '', 'more_than_one_page': False}
    local_search_template = loader.get_template('foods_local_search.html')
    local_search_w_results_template = loader.get_template('foods_local_search_+w_results+.html')

    cgi_params = get_cgi_params(request)
    search_query = cgi_params.get("search_query", '')
    if not search_query:
        return redirect("/foods/local_search/")
    retval = cast_int(cgi_params.get("page_size", PAGE_SIZE), 'page_size', local_search_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval
    retval = cast_int(cgi_params.get("page", PAGE_SIZE), 'page', local_search_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    current_page = retval
    if not search_query:
        return redirect("/foods/local_search/")
    kws = search_query.strip().split()

    # This is equivelant to q_term = (Q(food_name__icontains=kws[0]) & Q(food_name__icontains=kws[1]) & ... & Q(food_name__icontains=kws[-1]))
    q_term = reduce(and_, (Q(food_name__icontains=kw) for kw in kws))
    food_results = Food.objects.filter(q_term)
    food_objs.sort(key=attrgetter('food_name'))
    if not len(food_results):
        context["message"] = "No matches"
        return HttpResponse(local_search_template.render(context, request))
    elif len(food_results) <= page_size and current_page > 1:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        context["pagination_links"] = generate_pagination_links("/foods/local_search_results/", len(food_results), page_size, current_page, search_query=search_query)
        return HttpResponse(local_search_template.render(context, request))

    food_objs = [Food_Detailed.from_model_object(food_model_obj) for food_model_obj in food_results]
    if len(food_results) > page_size:
        context["more_than_one_page"] = True
        context["pagination_links"] = generate_pagination_links("/foods/local_search_results/", len(food_results), page_size, current_page, search_query=search_query)
        context['food_objs'] = slice_output_list_by_page(food_objs, page_size, current_page)
    else:
        context["more_than_one_page"] = False
        context['food_objs'] = food_objs
    return HttpResponse(local_search_w_results_template.render(context, request))
