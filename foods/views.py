#!/usr/bin/python

import random
import math

from decouple import config

from operator import and_, attrgetter

from functools import reduce

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.views.decorators.http import require_http_methods

from .models import Food
from utils import Food_Detailed, Navigation_Links_Displayer, generate_pagination_links, get_cgi_params, \
        slice_output_list_by_page, cast_to_int, Fdc_Api_Contacter, retrieve_pagination_params


navigation_links_displayer = Navigation_Links_Displayer({'/foods/': "Main Foods List",
                                                         "/foods/local_search/": "Local Food Search",
                                                         "/foods/fdc_search/": "FDC Food Search",
                                                         "/foods/add_food/": "Add Food Manually"})

DEFAULT_PAGE_SIZE = config("DEFAULT_PAGE_SIZE")

FDC_API_KEY = config("FDC_API_KEY")

VALID_SERVING_UNITS = ("cups", "floz", "g", "oz", "tbsp", "tsp")

FOOD_MODEL_OBJ_FLOAT_KEYS = ("serving_size", "energy_kcal", "biotin_B7_mcg", "calcium_mg", "cholesterol_mg",
                             "copper_mg", "dietary_fiber_g", "folate_B9_mcg", "iodine_mcg", "iron_mg", "magnesium_mg",
                             "niacin_B3_mg", "pantothenic_acid_B5_mg", "phosphorous_mg", "potassium_mg", "protein_g",
                             "riboflavin_B2_mg", "saturated_fat_g", "sodium_mg", "sugars_g", "thiamin_B1_mg",
                             "total_carbohydrates_g", "total_fat_g", "trans_fat_g", "vitamin_D_mcg", "vitamin_E_mg",
                             "zinc_mg")


@require_http_methods(["GET"])
def foods(request):
    foods_template = loader.get_template('foods/foods.html')
    context = {'more_than_one_page': False}

    retval = retrieve_pagination_params(foods_template, context, request, DEFAULT_PAGE_SIZE, query=False)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval["page_size"]
    page_number = retval["page_number"]

    food_objs = [Food_Detailed.from_model_obj(food_model_obj) for food_model_obj in Food.objects.filter()]
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
    context['subordinate_navigation'] = navigation_links_displayer.href_list_wo_one_callable("/foods/")
    context['food_objs'] = food_objs

    return HttpResponse(foods_template.render(context, request))


@require_http_methods(["GET"])
def foods_fdc_id(request, fdc_id):
    template = loader.get_template('foods/foods_+fdc_id+.html')
    food_model_objs = Food.objects.filter(fdc_id=fdc_id)
    if not len(food_model_objs):
        return HttpResponse(f"no object in 'foods' collection in 'nutritracker' data store with FDC ID {fdc_id}",
                            status=404)
    elif len(food_model_objs) > 1:
        return HttpResponse(f"inconsistent state: multiple objects matching query for FDC ID {fdc_id}", status=500)
    food_model_obj = food_model_objs[0]
    food_obj = Food_Detailed.from_model_obj(food_model_obj)
    subordinate_navigation = navigation_links_displayer.full_href_list_callable()
    context = {'food_obj': food_obj, 'food_or_recipe_obj': food_obj, 'subordinate_navigation': subordinate_navigation}
    return HttpResponse(template.render(context, request))


@require_http_methods(["GET"])
def foods_local_search(request):
    template = loader.get_template('foods/foods_local_search.html')
    subordinate_navigation = navigation_links_displayer.href_list_wo_one_callable("/foods/local_search/")
    context = {'subordinate_navigation': subordinate_navigation, 'message': '', 'more_than_one_page': False}
    return HttpResponse(template.render(context, request))


@require_http_methods(["GET", "POST"])
def foods_local_search_results(request):
    search_url = "/foods/local_search/"
    subordinate_navigation = navigation_links_displayer.full_href_list_callable()
    context = {'subordinate_navigation': subordinate_navigation, 'message': '', 'more_than_one_page': False}
    local_search_template = loader.get_template('foods/foods_local_search.html')
    local_search_results_template = loader.get_template('foods/foods_local_search_results.html')

    retval = retrieve_pagination_params(local_search_template, context, request, DEFAULT_PAGE_SIZE, search_url,
                                        query=True)
    if isinstance(retval, HttpResponse):
        return retval
    search_query = retval["search_query"]
    page_size = retval["page_size"]
    page_number = retval["page_number"]
    kws = search_query.strip().split()

    # This is equivelant to q_term = (Q(food_name__icontains=kws[0]) & Q(food_name__icontains=kws[1])
    #                                 & ... & Q(food_name__icontains=kws[-1]))
    q_term = reduce(and_, (Q(food_name__icontains=kw) for kw in kws))
    food_objs = list(Food.objects.filter(q_term))
    food_objs.sort(key=attrgetter('food_name'))
    if not len(food_objs):
        context["message"] = "No matches"
        return HttpResponse(local_search_template.render(context, request))
    elif len(food_objs) <= page_size and page_number > 1:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        context["pagination_links"] = generate_pagination_links("/foods/local_search_results/", len(food_objs),
                                                                page_size, page_number, search_query=search_query)
        return HttpResponse(local_search_template.render(context, request))

    food_objs = [Food_Detailed.from_model_obj(food_model_obj) for food_model_obj in food_objs]
    number_of_results = len(food_objs)
    number_of_pages = math.ceil(number_of_results / page_size)
    if page_number > number_of_pages:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        context["pagination_links"] = generate_pagination_links("/foods/local_search_results/", number_of_results,
                                                                page_size, page_number, search_query=search_query)
        return HttpResponse(local_search_results_template.render(context, request))

    if len(food_objs) > page_size:
        context["more_than_one_page"] = True
        context["pagination_links"] = generate_pagination_links("/foods/local_search_results/", len(food_objs),
                                                                page_size, page_number, search_query=search_query)
        context['food_objs'] = slice_output_list_by_page(food_objs, page_size, page_number)
    else:
        context["more_than_one_page"] = False
        context['food_objs'] = food_objs
    return HttpResponse(local_search_results_template.render(context, request))


@require_http_methods(["GET"])
def foods_fdc_search(request):
    template = loader.get_template('foods/foods_fdc_search.html')
    subordinate_navigation = navigation_links_displayer.href_list_wo_one_callable("/foods/fdc_search/")
    context = {'subordinate_navigation': subordinate_navigation, 'message': ''}
    return HttpResponse(template.render(context, request))


@require_http_methods(["GET", "POST"])
def foods_fdc_search_results(request, fdc_api_contacter=Fdc_Api_Contacter):
    search_url = "/foods/fdc_search/"
    api_contacter = fdc_api_contacter(FDC_API_KEY)
    subordinate_navigation = navigation_links_displayer.full_href_list_callable()
    context = {'subordinate_navigation': subordinate_navigation,
               'message': '',
               'more_than_one_page': False}
    fdc_search_template = loader.get_template('foods/foods_fdc_search.html')
    fdc_search_results_template = loader.get_template('foods/foods_fdc_search_results.html')

    retval = retrieve_pagination_params(fdc_search_template, context, request, DEFAULT_PAGE_SIZE, search_url,
                                        query=True)
    if isinstance(retval, HttpResponse):
        return retval
    search_query = retval["search_query"]
    page_size = retval["page_size"]
    page_number = retval["page_number"]

    number_of_results = api_contacter.number_of_search_results(query=search_query)
    if not number_of_results:
        context["message"] = "No matches"
        return HttpResponse(fdc_search_template.render(context, request))
    context["pagination_links"] = generate_pagination_links("/foods/fdc_search_results/", number_of_results, page_size,
                                                            page_number, search_query=search_query)
    if number_of_results < page_size * (page_number - 1) + 1:
        context["more_than_one_page"] = True
        context["message"] = "No more results"
        return HttpResponse(fdc_search_template.render(context, request))

    food_objs = api_contacter.search_by_keywords(query=search_query, page_size=page_size, page_number=page_number)
    for food_obj in food_objs:
        food_obj.in_db_already = bool(len(Food.objects.filter(fdc_id=food_obj.fdc_id)))
    context["more_than_one_page"] = number_of_results > page_size
    context['food_objs'] = food_objs
    return HttpResponse(fdc_search_results_template.render(context, request))


@require_http_methods(["GET"])
def foods_fdc_search_fdc_id(request, fdc_id):
    template = loader.get_template('foods/foods_fdc_search_+fdc_id+.html')
    subordinate_navigation = navigation_links_displayer.full_href_list_callable()
    context = {'subordinate_navigation': subordinate_navigation}

    api_contacter = Fdc_Api_Contacter(FDC_API_KEY)
    food_obj = api_contacter.look_up_fdc_id(fdc_id)
    if food_obj is None:
        return HttpResponse(f"No such FDC ID in the FoodData Central database: {fdc_id}", status=404)
    elif food_obj is False:
        return HttpResponse(f"Internal error in rendering food with ID {fdc_id}", status=500)
    food_obj.in_db_already = bool(len(Food.objects.filter(fdc_id=food_obj.fdc_id)))
    context['food_or_recipe_obj'] = context['food_obj'] = food_obj
    return HttpResponse(template.render(context, request))


@require_http_methods(["GET", "POST"])
def foods_fdc_import(request):
    template = loader.get_template('foods/foods_fdc_import.html')
    subordinate_navigation = navigation_links_displayer.full_href_list_callable()
    context = {'subordinate_navigation': subordinate_navigation, 'error': False}
    cgi_params = get_cgi_params(request)
    api_contacter = Fdc_Api_Contacter(FDC_API_KEY)

    retval = cast_to_int(cgi_params.get('fdc_id', 0), 'fdc_id', template, context, request, lowerb=1)
    if isinstance(retval, HttpResponse):
        return retval
    fdc_id = retval
    food_model_objs = list(Food.objects.filter(fdc_id=fdc_id))
    if len(food_model_objs):
        context['imported'] = False
        context['food_obj'] = food_model_objs[0]
        return HttpResponse(template.render(context, request))

    food_obj = api_contacter.look_up_fdc_id(fdc_id)
    if food_obj is None:
        context['error'] = True
        context['message'] = f"No such FDC ID in the FoodData Central database: {fdc_id}"
        return HttpResponse(template.render(context, request))

    context['imported'] = True
    food_model_cls_argd = food_obj.to_model_cls_args()
    food_model_obj = Food(**food_model_cls_argd)
    food_model_obj.save()

    context['food_obj'] = food_model_obj
    return HttpResponse(template.render(context, request))


@require_http_methods(["GET", "POST"])
def foods_add_food(request):
    template = loader.get_template('foods/foods_add_food.html')
    subordinate_navigation = navigation_links_displayer.href_list_wo_one_callable("/foods/add_food/")
    context = {'subordinate_navigation': subordinate_navigation, 'error': False, 'message': ''}
    cgi_params = get_cgi_params(request)

    if len(cgi_params):
        food_model_obj_argd = dict()
        try:
            food_model_obj_argd['food_name'] = cgi_params['food_name']
            assert len(food_model_obj_argd['food_name'])
        except (KeyError, AssertionError):
            context["error"] = True
            context["message"] = "value for 'food_name' required; must be a string at least 1 character long"
            return HttpResponse(template.render(context, request))
        try:
            food_model_obj_argd['serving_units'] = cgi_params['serving_units']
            assert food_model_obj_argd['serving_units'] in VALID_SERVING_UNITS
        except (KeyError, AssertionError):
            valid_serving_units_quoted = [f"'{unit}'" for unit in VALID_SERVING_UNITS]
            valid_serving_units_expr = ", ".join(valid_serving_units_quoted[:-1]) + ", or " + valid_serving_units_quoted[-1]
            context["error"] = True
            context["message"] = f"value for 'food_name' required; must be one of {valid_serving_units_expr}"
            return HttpResponse(template.render(context, request))
        for food_model_obj_key in FOOD_MODEL_OBJ_FLOAT_KEYS:
            try:
                food_model_obj_argd[food_model_obj_key] = float(cgi_params[food_model_obj_key])
                assert food_model_obj_argd[food_model_obj_key] >= 0
            except (KeyError, ValueError, AssertionError):
                context["error"] = True
                context["message"] = f"value for '{food_model_obj_key}' required; must be a decimal value greater than or equal to zero"
                return HttpResponse(template.render(context, request))
        food_model_obj_argd["fdc_id"] = 0
        food_model_obj_argd["nt_hash_id"] = hash(food_model_obj_argd['food_name'])
        while len(Food.objects.filter(nt_hash_id=food_model_obj_argd["nt_hash_id"])):
            food_model_obj_argd["nt_hash_id"] = hash(food_model_obj_argd['food_name'] + chr(random.randint(32,126)))
        food_model_obj = Food(**food_model_obj_argd)
        food_model_obj.save()
        return redirect(f"/foods/{food_model_obj_argd['nt_hash_id']}/")
    else:
        return HttpResponse(template.render(context, request))
