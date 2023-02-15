#!/usr/bin/python

import math

from bson.objectid import ObjectId, InvalidId

from decouple import config

from operator import and_, attrgetter

from functools import reduce

from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template import loader
from django.db.models import Q

from .models import Food, Recipe, Ingredient
from utils import Nutrient, Recipe_Detailed, Ingredient_Detailed, Food_Detailed, Navigation_Links_Displayer, \
        generate_pagination_links, slice_output_list_by_page, retrieve_pagination_params, get_cgi_params, cast_to_int


navigation_link_displayer = Navigation_Links_Displayer({'/recipes/': "Main Recipes List", '/recipes/search/': "Recipes Search", '/recipes/builder/': "Recipe Builder"})

default_page_size = config("DEFAULT_PAGE_SIZE")


# Much of this is adapted from foods.views.foods with just symbols changed,
# which is Not a Good Look. In the past I've generalized such code into
# higher-order functions and used a closure in each case of duplicated code. The
# downside is the code inside each higher-order function is created with a lot
# of find-and-replace and it becomes unreadable & unmaintainable. Not sure I
# want to go down the same path. When it's Don't Repeat Yourself vs. readable &
# maintainable code, I think the latter wins.


@require_http_methods(["GET", "POST"])
def recipes(request):
    recipes_template = loader.get_template('recipes/recipes.html')
    context = {'more_than_one_page': False, 'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/recipes/"), 'error': False, 'message': ''}

    retval = retrieve_pagination_params(recipes_template, context, request, default_page_size, query=False)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval["page_size"]
    page_number = retval["page_number"]

    recipe_objs = [Recipe_Detailed.from_model_obj(recipe_model_obj) for recipe_model_obj in Recipe.objects.filter()]
    recipe_objs = list(filter(lambda recipe_obj: recipe_obj.complete is True, recipe_objs))
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
    recipes_mongodb_id_template = loader.get_template('recipes/recipes_+mongodb_id+.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/recipes/"), 'error': False, 'message': ''}

    try:
        recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
    except (Recipe.DoesNotExist, InvalidId):
        context['error'] = True
        context['message'] = f"Error 404: no object in 'recipes' collection in 'nutritracker' data store with _id='{mongodb_id}'"
        return HttpResponse(recipes_mongodb_id_template.render(context, request), status=404)

    recipe_obj = Recipe_Detailed.from_json_obj(recipe_model_obj.serialize())
    context['recipe_obj'] = context['food_or_recipe_obj'] = recipe_obj
    return HttpResponse(recipes_mongodb_id_template.render(context, request))


@require_http_methods(["GET"])
def search(request):
    recipes_search_template = loader.get_template('recipes/recipes_search.html')
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/recipes/search/")
    context = {'subordinate_navigation': subordinate_navigation, 'message': '', 'more_than_one_page': False, 'error': False, 'message': ''}
    return HttpResponse(recipes_search_template.render(context, request))


@require_http_methods(["GET", "POST"])
def search_results(request):
    search_url = "/recipes/search/"
    subordinate_navigation = navigation_link_displayer.full_href_list_callable()
    context = {'subordinate_navigation': subordinate_navigation, 'message': '', 'more_than_one_page': False, 'error': False, 'message': ''}
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


@require_http_methods(["GET", "POST"])
def builder(request):
    recipes_builder_template = loader.get_template('recipes/recipes_builder.html')
    context = {'more_than_one_page': False, 'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/recipes/builder/"), 'error': False, 'message': ''}

    retval = retrieve_pagination_params(recipes_builder_template, context, request, default_page_size, query=False)
    if isinstance(retval, HttpResponse):
        return retval
    page_size = retval["page_size"]
    page_number = retval["page_number"]

    recipe_objs = [Recipe_Detailed.from_model_obj(recipe_model_obj) for recipe_model_obj in Recipe.objects.filter()]
    recipe_objs = list(filter(lambda recipe_obj: recipe_obj.complete is False, recipe_objs))
    recipe_objs.sort(key=attrgetter('recipe_name'))
    number_of_results = len(recipe_objs)
    number_of_pages = math.ceil(number_of_results / page_size)
    if page_number > number_of_pages:
        context["more_than_one_page"] = True
        context["message"] = "No recipes in the works"
        context["pagination_links"] = generate_pagination_links("/recipes/", number_of_results, page_size, page_number)
        return HttpResponse(recipes_builder_template.render(context, request))

    if len(recipe_objs) > page_size:
        recipe_objs = slice_output_list_by_page(recipe_objs, page_size, page_number)
        context["more_than_one_page"] = True
        context["pagination_links"] = generate_pagination_links("/recipes/", number_of_results, page_size, page_number)
    context['recipe_objs'] = recipe_objs

    return HttpResponse(recipes_builder_template.render(context, request))


@require_http_methods(["GET", "POST"])
def builder_new(request):
    cgi_params = get_cgi_params(request)
    builder_url = "/recipes/builder/new/"
    recipes_builder_new_template = loader.get_template('recipes/recipes_builder_new.html')
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/recipes/builder/"), 'error': False, 'message': ''}

    if not len(cgi_params.keys()):
        return HttpResponse(recipes_builder_new_template.render(context, request))
    else:
        recipe_name = cgi_params.get('recipe_name', None)
        if not recipe_name:
            return redirect(builder_url)
        recipe_model_obj = Recipe(recipe_name=recipe_name, complete=False, ingredients=list())
        recipe_model_obj.save()
        mongodb_id = recipe_model_obj._id
        return redirect(f"/recipes/builder/{mongodb_id}/")


@require_http_methods(["GET", "POST"])
def builder_mongodb_id(request, mongodb_id):
    cgi_params = get_cgi_params(request)
    recipes_builder_new_template = loader.get_template("recipes/recipes_builder_+mongodb_id+.html")
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/recipes/builder/"), "error": False, 'message': ''}

    try:
        recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
    except (Recipe.DoesNotExist, InvalidId):
        context["error"] = True
        context["message"] = f"Error 404: no object in 'recipes' collection in 'nutritracker' data store with _id='{mongodb_id}'"
        return HttpResponse(recipes_builder_new_template.render(context, request), status=404)

    context["food_or_recipe_obj"] = context["recipe_obj"] = Recipe_Detailed.from_model_obj(recipe_model_obj)
    return HttpResponse(recipes_builder_new_template.render(context, request))


@require_http_methods(["GET", "POST"])
def builder_mongodb_id_delete(request, mongodb_id):
    cgi_params = get_cgi_params(request)
    recipes_builder_mongodb_id_delete_template = loader.get_template("recipes/recipes_builder_+mongodb_id+_delete.html")
    context = {'subordinate_navigation': navigation_link_displayer.href_list_wo_one_callable("/recipes/builder/"), 'error': False, 'message': ''}

    button = cgi_params.get('button', None)
    if button != "Delete":
        return redirect(f"/recipes/builder/{mongodb_id}/")
    try:
        recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
    except (Recipe.DoesNotExist, InvalidId):
        context["error"] = True
        context["message"] = f"Error 404: no object in 'recipes' collection in 'nutritracker' data store with _id='{mongodb_id}'"
        return HttpResponse(recipes_builder_mongodb_id_delete_template.render(context, request), status=404)

    context["recipe_obj"] = Recipe_Detailed.from_model_obj(recipe_model_obj)
    recipe_model_obj.delete()
    return HttpResponse(recipes_builder_mongodb_id_delete_template.render(context, request))


@require_http_methods(["GET", "POST"])
def builder_mongodb_id_add_ingredient(request, mongodb_id):
    cgi_params = get_cgi_params(request)
    search_url = f"/recipes/builder/{mongodb_id}/"
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/recipes/builder/")
    context = {'subordinate_navigation': subordinate_navigation, 'more_than_one_page': False, 'saved': False, 'error': False, 'message': ''}
    builder_mongodb_id_add_ingredient_template = loader.get_template('recipes/recipes_builder_+mongodb_id+_add_ingredient.html')

    try:
        recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
    except (Recipe.DoesNotExist, InvalidId):
        context["error"] = True
        context["message"] = f"Error 404: no object in 'recipes' collection in 'nutritracker' data store with _id='{mongodb_id}'"
        return HttpResponse(builder_mongodb_id_add_ingredient_template.render(context, request), status=404)

    recipe_obj = Recipe_Detailed.from_model_obj(recipe_model_obj)
    context["recipe_obj"] = recipe_obj

    if len(cgi_params):
        retval = cast_to_int(cgi_params.get('fdc_id', ''), 'fdc_id', builder_mongodb_id_add_ingredient_template, context, request)
        if isinstance(retval, HttpResponse):
            return retval
        fdc_id = retval
        servings_number = cgi_params.get('servings_number', None)
        if not servings_number:
            return redirect(f"/recipes/builder/{recipe_obj.mongodb_id}/add_ingredient/")

        try:
            servings_number = float(servings_number)
            assert servings_number > 0
        except (ValueError, AssertionError):
            context["error"] = True
            context["message"] = "Error 422: value for 'servings_number' must be a floating-point number greater than zero"
            return HttpResponse(builder_mongodb_id_add_ingredient_template.render(context, request), status=422)

        try:
            food_model_obj = Food.objects.get(fdc_id=fdc_id)
        except Food.DoesNotExist:
            context["error"] = True
            context["message"] = f"Error 404: no object in 'foods' collection in 'nutritracker' data store with fdc_id='{fdc_id}'"
            return HttpResponse(builder_mongodb_id_add_ingredient_template.render(context, request), status=404)

        food_obj = Food_Detailed.from_model_obj(food_model_obj)
        context["food_objs"] = [food_obj]
        ingredient_obj = Ingredient(servings_number=servings_number, food=food_model_obj.serialize())
        recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
        recipe_model_obj.ingredients.append(ingredient_obj.serialize())
        recipe_model_obj.save()
        context["message"] = f"An ingredient of {servings_number}{food_obj.serving_units} of the {food_obj.food_name} has been added to your {recipe_obj.recipe_name} recipe."
        return HttpResponse(builder_mongodb_id_add_ingredient_template.render(context, request))
    else:
        retval = retrieve_pagination_params(builder_mongodb_id_add_ingredient_template, context, request, default_page_size, search_url, query=True)
        if isinstance(retval, HttpResponse):
            return retval
        search_query = retval["search_query"]
        page_size = retval["page_size"]
        page_number = retval["page_number"]
        kws = search_query.strip().split()

        try:
            recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
        except Recipe.DoesNotExist:
            context["error"] = True
            context["message"] = f"Error 404: no object in 'recipes' collection in 'nutritracker' data store with _id='{mongodb_id}'"
            return HttpResponse(builder_mongodb_id_add_ingredient_template.render(context, request), status=404)

        context["recipe_obj"] = Recipe_Detailed.from_model_obj(recipe_model_obj)

        # This is equivelant to q_term = (Q(recipe_name__icontains=kws[0]) & Q(recipe_name__icontains=kws[1]) & ... & Q(recipe_name__icontains=kws[-1]))
        q_term = reduce(and_, (Q(food_name__icontains=kw) for kw in kws))
        food_objs = list(Food.objects.filter(q_term))
        food_objs.sort(key=attrgetter('food_name'))
        if not len(food_objs):
            context["message"] = "No matches"
            return HttpResponse(builder_mongodb_id_add_ingredient_template.render(context, request))
        elif len(food_objs) <= page_size and page_number > 1:
            context["more_than_one_page"] = True
            context["message"] = "No more results"
            context["pagination_links"] = generate_pagination_links(f"recipes/builder/{mongodb_id}/add_ingredient/", len(food_objs), page_size, page_number, search_query=search_query)
            return HttpResponse(builder_mongodb_id_add_ingredient_template.render(context, request))

        food_objs = [Food_Detailed.from_model_obj(food_model_obj) for food_model_obj in food_objs]
        if len(food_objs) > page_size:
            context["more_than_one_page"] = True
            context["pagination_links"] = generate_pagination_links(f"recipes/builder/{mongodb_id}/add_ingredient/", len(food_objs), page_size, page_number, search_query=search_query)
            context['food_objs'] = slice_output_list_by_page(food_objs, page_size, page_number)
        else:
            context["more_than_one_page"] = False
            context['food_objs'] = food_objs
        return HttpResponse(builder_mongodb_id_add_ingredient_template.render(context, request))


def builder_mongodb_id_add_ingredient_fdc_id(request, mongodb_id, fdc_id):
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/recipes/builder/")
    context = {'subordinate_navigation': subordinate_navigation, 'error': False, 'message': ''}
    builder_mongodb_id_add_ingredient_fdc_id_template = loader.get_template('recipes/recipes_builder_+mongodb_id+_add_ingredient_+fdc_id+.html')

    try:
        recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
    except (Recipe.DoesNotExist, InvalidId):
        context["error"] = True
        context["message"] = f"Error 404: no object in 'recipes' collection in 'nutritracker' data store with _id='{mongodb_id}'"
        return HttpResponse(builder_mongodb_id_add_ingredient_fdc_id_template.render(context, request), status=404)

    context["recipe_obj"] = Recipe_Detailed.from_model_obj(recipe_model_obj)

    food_model_objs = Food.objects.filter(fdc_id=fdc_id)

    if not len(food_model_objs):
        context["error"] = True
        context["message"] = f"Error 404: no object in 'foods' collection in 'nutritracker' data store with fdc_id={fdc_id}"
        return HttpResponse(builder_mongodb_id_add_ingredient_fdc_id_template.render(context, request), status=404)
    elif len(food_model_objs) > 1:
        context["error"] = True
        context["message"] = f"Error 500: inconsistent state: multiple objects matching query for FDC ID {fdc_id}"
        return HttpResponse(builder_mongodb_id_add_ingredient_fdc_id_template.render(context, request), status=500)

    food_model_obj = food_model_objs[0]
    context['food_or_recipe_obj'] = context['food_obj'] = Food_Detailed.from_model_obj(food_model_obj)
    return HttpResponse(builder_mongodb_id_add_ingredient_fdc_id_template.render(context, request))


def builder_mongodb_id_add_ingredient_fdc_id_confirm(request, mongodb_id, fdc_id):
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/recipes/builder/")
    context = {'subordinate_navigation': subordinate_navigation, 'error': False, 'message': ''}
    builder_mongodb_id_add_ingredient_fdc_id_confirm_template = loader.get_template('recipes/recipes_builder_+mongodb_id+_add_ingredient_+fdc_id+_confirm.html')
    cgi_params = get_cgi_params(request)

    try:
        recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
    except (Recipe.DoesNotExist, InvalidId):
        context["error"] = True
        context["message"] = f"Error 404: no object in 'recipes' collection in 'nutritracker' data store with _id='{mongodb_id}'"
        return HttpResponse(builder_mongodb_id_add_ingredient_fdc_id_confirm_template.render(context, request), status=404)
    context["recipe_obj"] = Recipe_Detailed.from_model_obj(recipe_model_obj)

    try:
        food_model_obj = Food.objects.get(fdc_id=fdc_id)
    except Food.DoesNotExist:
        context["error"] = True
        context["message"] = f"Error 404: no object in 'foods' collection in 'nutritracker' data store with fdc_id={fdc_id}"
        return HttpResponse(builder_mongodb_id_add_ingredient_fdc_id_confirm_template.render(context, request), status=404)
    food_obj = Food_Detailed.from_model_obj(food_model_obj)

    servings_number = cgi_params.get('servings_number', None)
    if not servings_number:
        return redirect(f"/recipes/builder/{mongodb_id}/add_ingredient/")
    try:
        servings_number = float(servings_number)
        assert servings_number > 0
    except (ValueError, AssertionError):
        context["error"] = True
        context["message"] = "Error 422: value for 'servings_number' must be a floating-point number greater than zero"
        return HttpResponse(builder_mongodb_id_add_ingredient_fdc_id_confirm_template.render(context, request), status=422)

    context["servings_number"] = servings_number

    for nutrient_symbol in Nutrient.nutrient_symbols_to_numbers:
        nutrient_in_food = getattr(food_obj, nutrient_symbol, None)
        if nutrient_in_food is None:
            continue
        nutrient_in_food.amount *= servings_number
    food_obj.serving_size *= servings_number
    context['food_or_recipe_obj'] = context['food_obj'] = food_obj

    return HttpResponse(builder_mongodb_id_add_ingredient_fdc_id_confirm_template.render(context, request))


def builder_mongodb_id_finish(request, mongodb_id):
    subordinate_navigation = navigation_link_displayer.href_list_wo_one_callable("/recipes/builder/")
    context = {'subordinate_navigation': subordinate_navigation, 'error': False, 'message': ''}
    builder_mongodb_id_finish_template = loader.get_template('recipes/recipes_builder_+mongodb_id+_finish.html')

    try:
        recipe_model_obj = Recipe.objects.get(_id=ObjectId(mongodb_id))
    except (Recipe.DoesNotExist, InvalidId):
        context["error"] = True
        context["message"] = f"Error 404: no object in 'recipes' collection in 'nutritracker' data store with _id='{mongodb_id}'"
        return HttpResponse(builder_mongodb_id_finish_template.render(context, request), status=404)

    recipe_model_obj.complete = True
    recipe_model_obj.save()
    recipe_obj = Recipe_Detailed.from_model_obj(recipe_model_obj)
    context["food_or_recipe_obj"] = context["recipe_obj"] = Recipe_Detailed.from_model_obj(recipe_model_obj)

    return HttpResponse(builder_mongodb_id_finish_template.render(context, request))

