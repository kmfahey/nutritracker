#!/usr/bin/python

from operator import and_

from functools import reduce

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.db.models import Q

from .models import Food
from utils import Food_Detailed, Navigation_Links_Displayer


navigation_link_displayer = Navigation_Links_Displayer({'/foods/': "Main Foods List", "/foods/local_search/": "Local Food Search"})


def index(request):
    template = loader.get_template('foods.html')
    food_objs = [Food_Detailed.from_model_object(food_model_obj) for food_model_obj in Food.objects.filter()]
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/foods/")
    context = {'food_objs':food_objs, 'subordinate_navigation': subordinate_navigation}
    return HttpResponse(template.render(context, request))

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
    context = {'subordinate_navigation': subordinate_navigation, 'message':''}
    return HttpResponse(template.render(context, request))

def local_search_results(request):
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/foods/local_search/")
    context = {'subordinate_navigation': subordinate_navigation}
    local_search_template = loader.get_template('foods_local_search.html')
    local_search_w_results_template = loader.get_template('foods_local_search_+w_results+.html')
    if request.method == "GET":
        if not (set(request.GET.keys()) and 'search_query' in request.GET):
            return redirect("/foods/local_search/")
        search_query = request.GET.get("search_query")
    elif request.method == "POST":
        if not (set(request.POST.keys()) and 'search_query' in request.POST):
            return redirect("/foods/local_search/")
        search_query = request.POST.get("search_query")
    if not search_query:
        return redirect("/foods/local_search/")
    kws = search_query.strip().split()
    # This is equivelant to q_term = (Q(food_name__icontains=kws[0]) & Q(food_name__icontains=kws[1]) & ... & Q(food_name__icontains=kws[-1]))
    q_term = reduce(and_, (Q(food_name__icontains=kw) for kw in kws))
    food_results = Food.objects.filter(q_term)
    if not len(food_results):
        context["message"] = "No matches"
        return HttpResponse(local_search_template.render(context, request))
    else:
        context['food_objs'] = [Food_Detailed.from_model_object(food_model_obj) for food_model_obj in food_results]
        return HttpResponse(local_search_w_results_template.render(context, request))
