#!/usr/bin/python

from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from .models import Food
from utils import Food_Detailed


def index(request):
    template = loader.get_template('list_of_foods.html')
    food_objs = [Food_Detailed.from_model_object(food_model_obj) for food_model_obj in Food.objects.filter()]
    context = {'food_objs':food_objs}
    return HttpResponse(template.render(context, request))

def display_food(request, fdc_id):
    template = loader.get_template('individual_food_page.html')
    food_model_objs = Food.objects.filter(fdc_id=fdc_id)
    if not len(food_model_objs):
        return HttpResponse(f"no object in 'foods' collection in 'nutritracker' data store with FDC ID {fdc_id}", status=404)
    elif len(food_model_objs) > 1:
        return HttpResponse(f"inconsistent state: multiple objects matching query for FDC ID {fdc_id}", status=500)
    food_model_obj = food_model_objs[0]
    food_obj = Food_Detailed.from_model_object(food_model_obj)
    context = {'food_obj':food_obj}
    return HttpResponse(template.render(context, request))
