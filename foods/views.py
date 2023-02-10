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
