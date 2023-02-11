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

from .models import Food
from utils import Food_Detailed, Navigation_Links_Displayer, generate_pagination_links, get_cgi_params, slice_output_list_by_page, cast_to_int, Fdc_Api_Contacter


navigation_link_displayer = Navigation_Links_Displayer({'/foods/': "Main Foods List", "/foods/local_search/": "Local Food Search", "/foods/fdc_search/": "FDC Food Search"})

default_page_size = config("DEFAULT_PAGE_SIZE")
fdc_api_key = config("FDC_API_KEY")


@require_http_methods(["GET"])
def index(request):
    foods_template = loader.get_template('foods.html')
    cgi_params = get_cgi_params(request)
    context = {'more_than_one_page': False}

    retval = cast_to_int(cgi_params.get("page_size", default_page_size), 'page_size', foods_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval
    retval = cast_to_int(cgi_params.get("page_number", 1), 'page_number', foods_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_number = retval

    food_objs = [Food_Detailed.from_model_object(food_model_obj) for food_model_obj in Food.objects.filter()]
    food_objs.sort(key=attrgetter('food_name'))
    number_of_results = len(food_objs)
    number_of_pages = math.ceil(number_of_results / page_size)
    if page_number > number_of_pages:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        context["pagination_links"] = generate_pagination_links("/foods/", number_of_results, page_size, page_number)
        return HttpResponse(foods_template.render(context, request))

    if len(food_objs) > page_size:
        food_objs = slice_output_list_by_page(food_objs, page_size, page_number)
        context["more_than_one_page"] = True
        context["pagination_links"] = generate_pagination_links("/foods/", number_of_results, page_size, page_number)
    context['subordinate_navigation'] = navigation_link_displayer.href_list_wo_one_callable("/foods/")
    context['food_objs'] = food_objs

    return HttpResponse(foods_template.render(context, request))

@require_http_methods(["GET"])
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

@require_http_methods(["GET"])
def local_search(request):
    template = loader.get_template('foods_local_search.html')
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/foods/local_search/")
    context = {'subordinate_navigation': subordinate_navigation, 'message':'', 'more_than_one_page':False}
    return HttpResponse(template.render(context, request))

@require_http_methods(["GET","POST"])
def local_search_results(request):
    search_url = "/foods/local_search/"
    subordinate_navigation = navigation_link_displayer.full_href_list_callable()
    context = {'subordinate_navigation': subordinate_navigation, 'message': '', 'more_than_one_page': False}
    local_search_template = loader.get_template('foods_local_search.html')
    local_search_results_template = loader.get_template('foods_local_search_results.html')

    cgi_params = get_cgi_params(request)
    search_query = cgi_params.get("search_query", '')
    if not search_query:
        return redirect(search_url)
    retval = cast_to_int(cgi_params.get("page_size", default_page_size), 'page_size', local_search_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval
    retval = cast_to_int(cgi_params.get("page_number", 1), 'page_number', local_search_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_number = retval
    if not search_query:
        return redirect(search_url)
    kws = search_query.strip().split()

    # This is equivelant to q_term = (Q(food_name__icontains=kws[0]) & Q(food_name__icontains=kws[1]) & ... & Q(food_name__icontains=kws[-1]))
    q_term = reduce(and_, (Q(food_name__icontains=kw) for kw in kws))
    food_objs = list(Food.objects.filter(q_term))
    food_objs.sort(key=attrgetter('food_name'))
    if not len(food_objs):
        context["message"] = "No matches"
        return HttpResponse(local_search_template.render(context, request))
    elif len(food_objs) <= page_size and page_number > 1:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        context["pagination_links"] = generate_pagination_links("/foods/local_search_results/", len(food_objs), page_size, page_number, search_query=search_query)
        return HttpResponse(local_search_template.render(context, request))

    food_objs = [Food_Detailed.from_model_object(food_model_obj) for food_model_obj in food_objs]
    if len(food_objs) > page_size:
        context["more_than_one_page"] = True
        context["pagination_links"] = generate_pagination_links("/foods/local_search_results/", len(food_objs), page_size, page_number, search_query=search_query)
        context['food_objs'] = slice_output_list_by_page(food_objs, page_size, page_number)
    else:
        context["more_than_one_page"] = False
        context['food_objs'] = food_objs
    return HttpResponse(local_search_results_template.render(context, request))

@require_http_methods(["GET"])
def fdc_search(request):
    template = loader.get_template('foods_fdc_search.html')
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/foods/fdc_search/")
    context = {'subordinate_navigation': subordinate_navigation, 'message':''}
    return HttpResponse(template.render(context, request))

@require_http_methods(["GET","POST"])
def fdc_search_results(request):
    search_url = "/foods/fdc_search/"
    api_contacter = Fdc_Api_Contacter(fdc_api_key)
    subordinate_navigation = navigation_link_displayer.full_href_list_callable()
    context = {'subordinate_navigation': subordinate_navigation,
               'message': '',
               'more_than_one_page': False}
    fdc_search_template = loader.get_template('foods_fdc_search.html')
    fdc_search_results_template = loader.get_template('foods_fdc_search_results.html')

    query_params = dict()
    cgi_params = get_cgi_params(request)
    search_query = cgi_params.get("search_query", '')
    if not search_query:
        return redirect(search_url)
    retval = cast_to_int(cgi_params.get("page_size", default_page_size), 'page_size', fdc_search_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval
    retval = cast_to_int(cgi_params.get("page_number", 1), 'page_number', fdc_search_template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    page_number = retval
    query = search_query.strip().lower()

    number_of_results = api_contacter.number_of_search_results(query=query)
    if not number_of_results:
        context["message"] = "No matches"
        return HttpResponse(fdc_search_template.render(context, request))
    context["pagination_links"] = generate_pagination_links("/foods/fdc_search_results/", number_of_results, page_size, page_number, search_query=search_query)
    if number_of_results < page_size * (page_number - 1) + 1:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        return HttpResponse(fdc_search_template.render(context, request))

    food_objs = api_contacter.search_by_keywords(query=query, page_size=page_size, page_number=page_number)
    context["more_than_one_page"] = number_of_results > page_size
    context['food_objs'] = food_objs
    return HttpResponse(fdc_search_results_template.render(context, request))
