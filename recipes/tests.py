#!/usr/bin/python

import random
import html
import faker
import urllib.parse

from bson.objectid import ObjectId

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseRedirect
from django.test.client import RequestFactory
from django.test import TestCase, tag
from operator import attrgetter

from .models import Food, Ingredient, Recipe
from .views import recipes, recipes_mongodb_id, recipes_search, recipes_search_results, recipes_builder, \
        recipes_builder_new, recipes_builder_mongodb_id, recipes_builder_mongodb_id_delete, \
        recipes_builder_mongodb_id_remove_ingredient, recipes_builder_mongodb_id_add_ingredient


food_model_argds = {
    'White Bread': {
        'energy_kcal': 280, 'fdc_id': 2131541, 'food_name': 'White Bread', 'iron_mg': 3,  'protein_g': 8,
        'serving_size': 25, 'serving_units': 'g', 'sodium_mg': 540, 'sugars_g': 8, 'total_carbohydrates_g': 52,
        'total_fat_g': 2
    },
    'Whole Wheat Bread': {
        'calcium_mg': 47, 'dietary_fiber_g': 7, 'energy_kcal': 233, 'fdc_id': 1886332, 'folate_B9_mcg': 19,
        'food_name': 'Whole Wheat Bread', 'iron_mg': 2, 'niacin_B3_mg': 2, 'protein_g': 11, 'serving_size': 43,
        'serving_units': 'g', 'sodium_mg': 395, 'sugars_g': 6, 'total_carbohydrates_g': 44, 'total_fat_g': 3
    },
    'Peanut Butter': {
        'calcium_mg': 49.0, 'dietary_fiber_g': 5.0, 'energy_kcal': 598.0, 'fdc_id': 172470, 'folate_B9_mcg': 87.0,
        'food_name': 'Peanut Butter', 'iron_mg': 1.74, 'magnesium_mg': 168.0, 'niacin_B3_mg': 13.112,
        'pantothenic_acid_B5_mg': 1.137, 'phosphorous_mg': 335.0, 'potassium_mg': 558.0, 'protein_g': 22.21,
        'saturated_fat_g': 10.325, 'serving_size': 1.0, 'serving_units': 'cup', 'sodium_mg': 17.0, 'sugars_g': 10.49,
        'total_carbohydrates_g': 22.31, 'total_fat_g': 51.36, 'vitamin_E_mg': 9.1, 'zinc_mg': 2.51,
    },
    'Strawberry Jam': {
        'dietary_fiber_g': 1.0, 'energy_kcal': 37.0, 'fdc_id': 2009683, 'food_name': 'Strawberry Jam',
        'serving_size': 15.0, 'serving_units': 'g', 'sodium_mg': 1.5, 'sugars_g': 8.0, 'total_carbohydrates_g': 9.0
    },
    'Butter': {
         'cholesterol_mg': 30, 'energy_kcal': 100.0, 'fdc_id': 2094280, 'food_name': 'Butter', 'protein_g': 1.0,
         'saturated_fat_g': 7, 'serving_size': 14.0, 'serving_units': 'g', 'sodium_mg': 95.1, 'total_fat_g': 11.0
    },
    'Honey': {
        'calcium_mg': 6, 'energy_kcal': 304, 'fdc_id': 169640, 'folate_B9_mcg': 2, 'food_name': 'Honey',
        'magnesium_mg': 2, 'phosphorous_mg': 4, 'potassium_mg': 52, 'serving_size': 1, 'serving_units': 'cup',
        'sodium_mg': 4, 'sugars_g': 82, 'total_carbohydrates_g': 82
    },
}

recipe_ingredients = {
    'Peanut Butter & Jam Sandwich': {
        'White Bread': 3.04, 'Peanut Butter': 0.1268025851, 'Strawberry Jam': 2.626666667
    },
    'Peanut Butter Sandwich': {
        'Whole Wheat Bread': 2, 'Peanut Butter': 0.1268025851
    },
    'Peanut Butter & Butter Sandwich': {
        'White Bread': 3.04, 'Peanut Butter': 0.1268025851, 'Butter': 4
    },
    'Peanut Butter & Honey Sandwich': {
        'White Bread': 3.04, 'Peanut Butter': 0.1268025851, 'Honey': 0.04226752838
    }
}


def _generate_bogus_mongodb_id(model_class):
    # A bogus ObjectId must have 24 digits in hex to be taken as a valid object.
    bogus_mongodb_id = ObjectId(str(hex(random.randint(0x100000000000000000000000,
                                                       0xffffffffffffffffffffffff))).removeprefix("0x"))
    # Just in case by random chance a valid object id was picked.
    while len(model_class.objects.filter(_id=bogus_mongodb_id)):
        bogus_mongodb_id = ObjectId(str(hex(random.randint(0x100000000000000000000000,
                                                           0xffffffffffffffffffffffff))).removeprefix("0x"))
    return bogus_mongodb_id

def floatformat(floatval):
    return round(floatval) if floatval == round(floatval) else round(floatval, 1)


@tag("recipes")
class recipes_test_case(TestCase):

    def setUp(self):
        self.faker_obj = faker.Faker()

        # Instancing fake user
        self.test_username = self.faker_obj.user_name()
        self.test_password = self.faker_obj.password()
        self.test_user = User.objects.create_user(username=self.test_username, password=self.test_password)
        self.test_user.save()

        # Building the testing Recipe objects
        #
        # Instancing every Food object from the stored argds, saving them to the
        # db, and then saving them to self.foods
        self.foods = dict()
        for food_name, food_model_argd in food_model_argds.items():
            food_model_obj = Food(**food_model_argd)
            food_model_obj.save()
            self.foods[food_name] = food_model_obj

        # Instancing every Recipe object by way of Food objects and Ingredient objects
        self.ingredients = list()
        self.recipes = dict()

        # Iterating over the recipe_ingredients dict, which associates recipe
        # names to dicts that associate food names to servings_number values (an
        # Ingredient property).
        for recipe_name, food_names_to_servings_numbers in recipe_ingredients.items():

            # Instancing the Recipe object with an empty ingredients property
            recipe_model_obj = Recipe(owner=self.test_username, recipe_name=recipe_name, complete=False, ingredients=list())

            # For each food name & servings number, instance an Ingredient
            # object from that, save it, then append it to the working Recipe
            # object's ingredients property.
            for food_name, servings_number in food_names_to_servings_numbers.items():
                food_model_obj = self.foods[food_name]
                ingredient_model_obj = Ingredient(servings_number=servings_number, food=food_model_obj.serialize())
                ingredient_model_obj.save()
                self.ingredients.append(ingredient_model_obj)
                recipe_model_obj.ingredients.append(ingredient_model_obj.serialize())

            # Finish & save the working Recipe object, then add it to the
            # self.recipes dict by name.
            recipe_model_obj.complete = True
            recipe_model_obj.save()
            self.recipes[recipe_name] = recipe_model_obj

        self.request_factory = RequestFactory()

    def _middleware_and_user_bplate(self, request):
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        request.user = authenticate(username=self.test_username, password=self.test_password)
        login(request, request.user)
        return request

    def tearDown(self):
        for recipe_model_obj in Recipe.objects.filter():
            recipe_model_obj.delete()
        for ingredient_model_obj in Ingredient.objects.filter():
            ingredient_model_obj.delete()
        for food_model_obj in Food.objects.filter():
            food_model_obj.delete()


class test_recipes(recipes_test_case):

    def test_recipes_normal_case(self):
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/")
        )
        content = recipes(request).content.decode('utf-8')
        for recipe_name in self.recipes.keys():
            recipe_name_esc = html.escape(recipe_name)
            assert recipe_name_esc in content, 'calling recipes(request) does not yield content containing the ' \
                    f'"recipe name "{recipe_name}" although it is in the data store and should be listed'

    def test_recipes_error_case_pagination_overshooting_arg(self):
        cgi_data = {"page_size": 2, "page_number": 4}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/", data=cgi_data)
        )
        content = recipes(request).content.decode('utf-8')
        assert "No more results" in content, f"calling recipes(request) with CGI params '{cgi_query_string}' that " \
                "should point to a page off the end of the recipes list didn't yield content containing " \
                "appropriate error message"
        assert '<a href="/recipes/?page_size=2&page_number=2">2</a>' in content, f"calling recipes(request) with " \
                f"cgi params '{cgi_query_string}' that should point to a page off the end of the recipes list didn't " \
                "yield content containing correct pagination links"

    def test_recipes_normal_case_pagination(self):
        cgi_data = {"page_size": 2, "page_number": 1}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/", data=cgi_data)
        )
        content = recipes(request).content.decode('utf-8')
        recipe_names = sorted(self.recipes.keys())
        for recipe_name in recipe_names[0:2]:
            recipe_name_esc = html.escape(recipe_name)
            assert recipe_name_esc in content, f"calling recipes(request) with CGI params '{cgi_query_string}' does " \
                    f'not yield content containing the recipe name "{recipe_name}" although it is in the data store ' \
                    'and should be listed'
        for recipe_name in recipe_names[2:]:
            recipe_name_esc = html.escape(recipe_name)
            assert recipe_name_esc not in content, f"calling recipes(request) with CGI params '{cgi_query_string}' " \
                    'yields content containing the recipe name "{recipe_name}" although the params should put ' \
                    'it on a later page'
        assert '<a href="/recipes/?page_size=2&page_number=2">2</a>' in content, "calling recipes(request) with " \
                f"cgi params '{cgi_query_string}' didn't yield content containing correct pagination links"

    def test_recipes_error_case_user_not_logged_in(self):
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/")
        )
        logout(request)
        content = recipes(request).content.decode('utf-8')
        assert "You are not logged in; no recipes to display." in content, "calling recipes(request) without a " \
                "logged-in user doesn't yield content with the appropriate error message"
        for recipe_name in self.recipes:
            assert html.escape(recipe_name) not in content, f"calling recipes(request) without a logged-in user " \
                    f"yields content that lists at least one recipe (in this case, '{recipe_name}'"


class test_recipes_mongodb_id(recipes_test_case):

    def test_recipes_mongodb_id_normal_case(self):
        # A bogus ObjectId must have 24 digits in hex to be taken as a valid object.
        bogus_mongodb_id = ObjectId(str(hex(random.randint(0x100000000000000000000000,
                                                           0xffffffffffffffffffffffff))).removeprefix("0x"))
        # Just in case by random chance a valid object id was picked.
        while len(Recipe.objects.filter(_id=bogus_mongodb_id)):
            bogus_mongodb_id = ObjectId(str(hex(random.randint(0x100000000000000000000000,
                                                               0xffffffffffffffffffffffff))).removeprefix("0x"))
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/{bogus_mongodb_id}")
        )
        response = recipes_mongodb_id(request, bogus_mongodb_id)
        content = response.content.decode('utf-8')
        error_message = html.escape("Error 404: no object in 'recipes' collection in 'nutritracker' data store "
                                        f"with _id='{bogus_mongodb_id}'")
        assert response.status_code == 404, f"calling recipes_mongodb_id(request, '{bogus_mongodb_id}'), where that " \
                "object id is not associated with any Recipe object, doesn't yield a response with status code == 404"
        assert error_message in content, f"calling recipes_mongodb_id(request, '{bogus_mongodb_id}'), where that " \
                "object id is not associated with any Recipe object, doesn't yield content containing the " \
                "appropriate error message"


class test_recipes_search(recipes_test_case):

    # recipes_search() is a static page, so all there is to test is if it returns a response with status code 200.
    def test_recipes_search_normal_case(self):
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/search/")
        )
        response = recipes_search(request)
        assert response.status_code == 200, "calling recipes_search() doesn't yield a response with status code == 200"


class test_recipes_search_results(recipes_test_case):

    def test_recipes_search_results_normal_case(self):
        cgi_data = {"search_query": "Honey", "page_size": 25, "page_number": 1}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/search_results/", data=cgi_data)
        )
        content = recipes_search_results(request).content.decode('utf-8')
        for recipe_name in self.recipes:
            recipe_name_esc = html.escape(recipe_name)
            if "Honey" in recipe_name:
                assert recipe_name_esc in content, f'calling recipes_search_results(request) with CGI params ' \
                        f"'{cgi_query_string}' does not yield content containing the recipe name '{recipe_name}' " \
                        'although it is a match and should be listed'
            else:
                assert recipe_name_esc not in content, f'calling recipes_search_results(request) with CGI params ' \
                        f"'{cgi_query_string}' yields content containing the recipe name '{recipe_name}' although it " \
                        'is not a match and should not be listed'

    def test_recipes_search_results_normal_case_no_matches(self):
        cgi_data = {"search_query": "Pickle", "page_size": 25, "page_number": 1}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/search_results/", data=cgi_data)
        )
        content = recipes_search_results(request).content.decode('utf-8')
        assert "No matches" in content, f'calling recipes_search_results(request) with CGI params ' \
                        f"'{cgi_query_string}' does not yield content containing the string 'No matches' " \
                        'even though there should be no matches based on the extant Recipe objects'
        for recipe_name in self.recipes:
            recipe_name_esc = html.escape(recipe_name)
            assert recipe_name_esc not in content, f'calling recipes_search_results(request) with CGI params ' \
                    f"'{cgi_query_string}' yields content containing the recipe name '{recipe_name}' although it " \
                    'is not a match and should not be listed'

    def test_recipes_search_results_error_case_pagination_overshooting_arg(self):
        cgi_data = {"page_size": 2, "page_number": 4, "search_query": "Butter"}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/search_results/", data=cgi_data)
        )
        content = recipes_search_results(request).content.decode('utf-8')
        assert "No more results" in content, "calling recipes_search_results(request) with CGI params " \
                f"'{cgi_query_string}' that should point to a page off the end of the recipes list didn't yield " \
                "content containing message 'No more results'"
        assert '<a href="/recipes/search_results/?page_size=2&page_number=2&search_query=Butter">2</a>' in content, \
                f"calling recipes_search_results(request) with CGI params '{cgi_query_string}' that should point " \
                "to a page off the end of the search results didn't yield content containing correct pagination links"


class test_recipes_builder(recipes_test_case):

    def setUp(self):
        super().setUp()
        for recipe_model_obj in self.recipes.values():
            recipe_model_obj.complete = False
            recipe_model_obj.save()

    def test_recipes_builder_normal_case(self):
        recipe_model_objs = sorted(self.recipes.values(), key=attrgetter('recipe_name'))
        for recipe_model_obj in recipe_model_objs[2:]:
            recipe_model_obj.complete = True
            recipe_model_obj.save()
        cgi_data = {"page_size": 25, "page_number": 1}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/builder/", data=cgi_data)
        )
        content = recipes_builder(request).content.decode('utf-8')
        for recipe_model_obj in recipe_model_objs[:2]:
            assert html.escape(recipe_model_obj.recipe_name) in content, "having set up the recipe model object " \
                    f"by name '{recipe_model_obj.recipe_name}' to have attribute completed=False, calling " \
                    f"recipes_builder(request) with CGI params '{cgi_query_string}' does not yield content containing " \
                    "that recipe_name string value"
        for recipe_model_obj in recipe_model_objs[2:]:
            assert html.escape(recipe_model_obj.recipe_name) not in content, "with the recipe model object by name " \
                    f"'{recipe_model_obj.recipe_name}' having attribute completed=True, calling " \
                    f"recipes_builder(request) with CGI params '{cgi_query_string}' yields content containing that " \
                    "recipe_name string value"

    def test_recipes_builder_normal_case_no_recipes_to_display(self):
        for recipe_model_obj in self.recipes.values():
            recipe_model_obj.complete = True
            recipe_model_obj.save()
        cgi_data = {"page_size": 25, "page_number": 1}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/builder/", data=cgi_data)
        )
        content = recipes_builder(request).content.decode('utf-8')
        assert "No recipes in the works" in content, "calling recipes_builder(request) with CGI params " \
                f"'{cgi_query_string}', where all extant Recipe objects have the attribute complete=True, " \
                "doesn't yield content containing message 'No recipes in the works'"
        for recipe_model_obj in self.recipes.values():
            assert html.escape(recipe_model_obj.recipe_name) not in content, f"calling recipes_builder(request) " \
                    f"with CGI params '{cgi_query_string}', where all extant Recipe objects have the attribute " \
                    "complete=True, yields content containing the recipe_name string value " \
                    f"'{recipe_model_obj.recipe_name}'"

    def test_recipes_builder_error_case_pagination_overshooting_arg(self):
        cgi_data = {"page_size": 2, "page_number": 4}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/builder/", data=cgi_data)
        )
        content = recipes_builder(request).content.decode('utf-8')
        assert "No more recipes" in content, "calling recipes_builder(request) with CGI params " \
                f"'{cgi_query_string}' that should point to a page off the end of the recipes list didn't yield " \
                "content containing message 'No more results'"
        assert '<a href="/recipes/builder/?page_size=2&page_number=2">2</a>' in content, \
                f"calling recipes_search_results(request) with CGI params '{cgi_query_string}' that should point " \
                "to a page off the end of the search results didn't yield content containing correct pagination links"

    def test_recipes_builder_pagination_error_case_bad_arg(self):
        cgi_data = {'page_number': 'one', 'page_size': 10}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/builder/", data=cgi_data)
        )
        content = recipes_builder(request).content.decode('utf-8')
        assert "value for page_number must be an integer; received &#x27;one&#x27;" in content, \
                f"calling recipes_builder() with CGI params '{cgi_query_string}'  did not produce the correct error"


class test_recipes_builder_new(recipes_test_case):

    # When called with no CGI params recipes_builder_new() displays a static
    # page, so all there is to test is that status code is 200.
    def test_recipes_builder_new_normal_case_no_args(self):
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/builder/new/")
        )
        response = recipes_builder_new(request)
        assert response.status_code == 200, "calling recipes_builder_new() with no CGI params doesn't yield a " \
                "response with status code == 200"

    def test_recipes_builder_new_normal_case_w_recipe_name_arg(self):
        cgi_data = {"recipe_name": "Peanut Butter & Jam & Butter Sandwich"}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/builder/new/", data=cgi_data)
        )
        response = recipes_builder_new(request)
        assert isinstance(response, HttpResponseRedirect), f"calling recipes_builder_new() with CGI params " \
                f"'{cgi_query_string}' doesn't return a redirect"
        try:
            recipe_model_obj = Recipe.objects.get(recipe_name=cgi_data["recipe_name"])
        except Recipe.DoesNotExist:
            raise AssertionError(f"calling recipes_builder_new() with CGI params '{cgi_query_string}' doesn't instance "
                                 "& save a Recipe object to the data store with that recipe name")
        assert response.url == f"/recipes/builder/{recipe_model_obj._id}/", f"calling recipes_builder_new() with CGI " \
                f"params '{cgi_query_string}' creates & saves a Recipe object by that name, but returns a redirect " \
                "that doesn't point to the correct url including that object's ObjectId"

    def test_recipes_builder_new_error_case_bad_recipe_name_arg(self):
        cgi_data = {"recipe_name": ""}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get("/recipes/builder/new/", data=cgi_data)
        )
        response = recipes_builder_new(request)
        assert not isinstance(response, HttpResponseRedirect), f"calling recipes_builder_new() with CGI params " \
                f"'{cgi_query_string}' returns a redirect instead a page with content containing an error message"
        content = response.content.decode('utf-8')
        error_message = "value for recipe_name must be a string with length greater than 1 characters long"
        assert error_message in content, f"calling recipes_builder_new() with CGI params '{cgi_query_string}' does " \
                "not yield content containing the appropriate error message"


class test_recipes_builder_mongodb_id(recipes_test_case):

    def test_recipes_builder_mongodb_id_normal_case(self):
        recipe_name = "Peanut Butter & Jam & Butter Sandwich" 
        recipe_model_obj = Recipe(recipe_name=recipe_name, complete=False, ingredients=list())
        recipe_model_obj.save()
        mongodb_id = recipe_model_obj._id
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{mongodb_id}/")
        )
        response = recipes_builder_mongodb_id(request, mongodb_id)
        assert response.status_code == 200, "calling recipes_builder_mongodb_id() with an objectid associated with " \
                "an extant Recipe object doesn't yield a response with status code == 200"

    def test_recipes_builder_mongodb_id_error_case_invalid_mongodb_id(self):
        # A bogus ObjectId must have 24 digits in hex to be taken as a valid object.
        bogus_mongodb_id = ObjectId(str(hex(random.randint(0x100000000000000000000000,
                                                           0xffffffffffffffffffffffff))).removeprefix("0x"))
        # Just in case by random chance a valid object id was picked.
        while len(Recipe.objects.filter(_id=bogus_mongodb_id)):
            bogus_mongodb_id = ObjectId(str(hex(random.randint(0x100000000000000000000000,
                                                               0xffffffffffffffffffffffff))).removeprefix("0x"))
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{bogus_mongodb_id}/")
        )
        response = recipes_builder_mongodb_id(request, bogus_mongodb_id)
        assert response.status_code == 404, "calling recipes_builder_mongodb_id() with an invalid objectid that " \
                "doesn't correspond to any Recipe object doesn't yield a response with status code 404"
        content = response.content.decode('utf-8')
        error_message = "Error 404: no object in &#x27;recipes&#x27; collection in &#x27;nutritracker&#x27; data " \
                f"store with _id=&#x27;{bogus_mongodb_id}&#x27;"
        assert error_message in content, "calling recipes_builder_mongodb_id() with an invalid objectid that " \
                "doesn't correspond to any Recipe object doesn't yield content containing the appropriate error " \
                "message"


class test_recipes_builder_mongodb_id_delete(recipes_test_case):

    def test_recipes_builder_mongodb_id_delete_normal_case(self):
        mongodb_id = random.choice(list(self.recipes.values()))._id
        cgi_data = {"button": "Delete"}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{mongodb_id}/delete/", data=cgi_data)
        )
        response = recipes_builder_mongodb_id_delete(request, mongodb_id)
        assert not isinstance(response, HttpResponseRedirect), f"calling recipes_builder_mongodb_id_delete() with " \
                f"CGI params '{cgi_query_string}' and a valid MongoDB id returns a redirect when it shouldn't"
        assert response.status_code == 200
        assert not any(recipe_model_obj._id == mongodb_id for recipe_model_obj in Recipe.objects.filter()), \
                f"calling recipes_builder_mongodb_id_delete() with CGI params '{cgi_query_string}' and a valid " \
                "MongoDB id fails to delete from the database the Recipe object with that id"

    def test_recipes_builder_mongodb_id_delete_error_case_wo_button(self):
        mongodb_id = random.choice(list(self.recipes.values()))._id
        cgi_query_string = urllib.parse.urlencode({"button": "Delete"})
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{mongodb_id}/delete/")
        )
        response = recipes_builder_mongodb_id_delete(request, mongodb_id)
        assert isinstance(response, HttpResponseRedirect), f"calling recipes_builder_mongodb_id_delete() without " \
                f"the CGI params '{cgi_query_string}' doesn't return a redirect"
        assert response.url == f"/recipes/builder/{mongodb_id}/", f"calling recipes_builder_mongodb_id_delete() " \
                f"without the CGI params '{cgi_query_string}' doesn't return a redirect to the appropriate URL"
        try:
            Recipe.objects.get(_id=ObjectId(mongodb_id))
        except Recipe.DoesNotExist:
            raise AssertionError("calling recipes_builder_mongodb_id_delete() with a valid object id but without " 
                "the CGI params '{cgi_query_string}' nevertheless deletes the Recipe object with that id.")

    def test_recipes_builder_mongodb_id_delete_error_case_invalid_mongodb_id(self):
        bogus_mongodb_id = _generate_bogus_mongodb_id(Recipe)
        cgi_data = {"button": "Delete"}
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{bogus_mongodb_id}/delete/", data=cgi_data)
        )
        response = recipes_builder_mongodb_id_delete(request, bogus_mongodb_id)
        assert response.status_code == 404, "calling recipes_builder_mongodb_id_delete() with an invalid objectid " \
                "that doesn't correspond to any Recipe object doesn't yield a response with status code 404"
        content = response.content.decode('utf-8')
        error_message = "Error 404: no object in &#x27;recipes&#x27; collection in &#x27;nutritracker&#x27; data " \
                f"store with _id=&#x27;{bogus_mongodb_id}&#x27;"
        assert error_message in content, "calling recipes_builder_mongodb_id_delete() with an invalid objectid " \
                "that doesn't correspond to any Recipe object doesn't yield content containing the appropriate " \
                "error message"


class test_recipes_builder_mongodb_id_remove_ingredient(recipes_test_case):

    def test_recipes_builder_mongodb_id_remove_ingredient_normal_case(self):
        recipe_model_obj = self.recipes['Peanut Butter & Jam Sandwich']
        food_model_obj = self.foods['Strawberry Jam']
        for serialized_ingredient_obj in recipe_model_obj.ingredients:
            if serialized_ingredient_obj['food']['fdc_id'] == food_model_obj.fdc_id:
                ingredient_model_obj = Ingredient.objects.get(_id=ObjectId(serialized_ingredient_obj['_id']))
                break
        cgi_data = {"fdc_id": food_model_obj.fdc_id}
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{recipe_model_obj._id}/delete/", data=cgi_data)
        )
        content = recipes_builder_mongodb_id_remove_ingredient(request, recipe_model_obj._id).content.decode('utf-8')
        ingredient_serving_qty = floatformat(ingredient_model_obj.servings_number * food_model_obj.serving_size)
        deletion_message = f'The ingredient of {ingredient_serving_qty}{food_model_obj.serving_units} ' \
                f'of the <a href="/recipes/builder/{recipe_model_obj._id}/add_ingredient/{food_model_obj.fdc_id}/">' \
                f'{food_model_obj.food_name}</a> has been removed from your ' \
                f'{html.escape(recipe_model_obj.recipe_name)} recipe.'
        assert deletion_message in content, "calling recipes_builder_mongodb_id_remove_ingredient() " \
                "with a Recipe object's mongodb_id and the fdc_id of an ingredient in that recipe doesn't yield " \
                "content containing the appropriate deletion message"
        recipe_model_obj.refresh_from_db()
        assert not any(serialized_ingredient_obj['food']['fdc_id'] == food_model_obj.fdc_id
                       for serialized_ingredient_obj in recipe_model_obj.ingredients), \
                "calling recipes_builder_mongodb_id_remove_ingredient() with a Recipe object's mongodb_id and the " \
                "fdc_id of an ingredient in that recipe doesn't remove that ingredient from the Recipe object"

    def test_recipes_builder_mongodb_id_remove_ingredient_error_case_invalid_mongodb_id(self):
        bogus_mongodb_id = _generate_bogus_mongodb_id(Recipe)
        food_model_obj = random.choice(list(Food.objects.filter()))
        cgi_data = {"fdc_id": food_model_obj.fdc_id}
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{bogus_mongodb_id}/remove_ingredient/", data=cgi_data)
        )
        response = recipes_builder_mongodb_id_remove_ingredient(request, bogus_mongodb_id)
        assert response.status_code == 404, "calling recipes_builder_mongodb_id_remove_ingredient() with an " \
                "invalid objectid that doesn't correspond to any Recipe object doesn't yield a response with status code 404"
        content = response.content.decode('utf-8')
        error_message = "Error 404: no object in &#x27;recipes&#x27; collection in &#x27;nutritracker&#x27; data " \
                f"store with _id=&#x27;{bogus_mongodb_id}&#x27;"
        assert error_message in content, "calling recipes_builder_mongodb_id_remove_ingredient() with an invalid " \
                "objectid that doesn't correspond to any Recipe object doesn't yield content containing the " \
                "appropriate error message"

    def test_recipes_builder_mongodb_id_remove_ingredient_error_case_nonconformant_fdc_id_arg(self):
        fdc_id = -1
        cgi_data = {"fdc_id": fdc_id}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        recipe_model_obj = random.choice(list(self.recipes.values()))
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{recipe_model_obj._id}/delete/", data=cgi_data)
        )
        content = recipes_builder_mongodb_id_remove_ingredient(request, recipe_model_obj._id).content.decode('utf-8')
        error_message = "value for fdc_id must be an integer greater than or equal to 1; received &#x27;-1&#x27;"
        assert error_message in content, f"calling recipes_builder_mongodb_id_remove_ingredient() with a valid " \
                f"Recipe objectid and CGI params '{cgi_query_string}' does not yield content containing the " \
                "appropriate error message"

    def test_recipes_builder_mongodb_id_remove_ingredient_error_case_invented_fdc_id(self):
        recipe_model_obj = random.choice(list(self.recipes.values()))
        fdc_ids = [serialized_ingredient_obj['food']['fdc_id'] for serialized_ingredient_obj in recipe_model_obj.ingredients]
        spurious_fdc_id = random.randint(2**17, 2**22)
        while spurious_fdc_id in fdc_ids:
            spurious_fdc_id = random.randint(2**17, 2**22)
        cgi_data = {"fdc_id": spurious_fdc_id}
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{recipe_model_obj._id}/remove_ingredient/", data=cgi_data)
        )
        content = recipes_builder_mongodb_id_remove_ingredient(request, recipe_model_obj._id).content.decode('utf-8')
        error_message = f"recipe with _id=&#x27;{recipe_model_obj._id}&#x27; has no ingredient with " \
                f"fdc_id=&#x27;{spurious_fdc_id}&#x27;"
        assert error_message in content, "calling recipes_builder_mongodb_id_remove_ingredient() with a valid " \
                "Recipe objectid and an invalid fdc_id does not yield content containing the appropriate error message"


class test_recipes_builder_mongodb_id_add_ingredient(recipes_test_case):

    def test_recipes_builder_mongodb_id_add_ingredient_normal_case(self):
        recipe_model_obj = self.recipes['Peanut Butter & Jam Sandwich']
        # This is the official way to copy a model object: set its pk (ie.
        # primary key) attribute to None and its _state.adding attribute to
        # True.
        recipe_model_obj.pk = None
        recipe_model_obj._state.adding = True
        recipe_model_obj.recipe_name = "Peanut Butter & Jam & Butter Sandwich"
        recipe_model_obj.complete = False
        recipe_model_obj.save()
        food_model_obj = Food.objects.get(food_name="Butter")
        cgi_data = {'fdc_id': food_model_obj.fdc_id, 'servings_number': 4}
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{recipe_model_obj._id}/add_ingredient/", data=cgi_data)
        )
        content = recipes_builder_mongodb_id_add_ingredient(request, recipe_model_obj._id).content.decode('utf-8')
        recipe_model_obj.refresh_from_db()
        ingredient_serving_qty = floatformat(cgi_data["servings_number"] * food_model_obj.serving_size)
        success_message = f'An ingredient of {ingredient_serving_qty}{food_model_obj.serving_units} of ' \
                f'the <a href="/recipes/builder/{recipe_model_obj._id}/add_ingredient/{food_model_obj.fdc_id}/">' \
                f'{html.escape(food_model_obj.food_name)}</a> has been added to your ' \
                f'{html.escape(recipe_model_obj.recipe_name)} recipe. ' \
                f'<a href="/recipes/builder/{recipe_model_obj._id}/">Click here</a> to add another ingredient, ' \
                'finish the recipe, or delete it.'
        assert success_message in content, "calling recipes_builder_mongodb_id_add_ingredient() " \
                "with a Recipe object's mongodb_id and the fdc_id of an ingredient to add to that recipe doesn't yield " \
                "content containing the appropriate addition message"
        assert any(serialized_ingredient_obj['food']['fdc_id'] == food_model_obj.fdc_id
                   for serialized_ingredient_obj in recipe_model_obj.ingredients), \
                "calling recipes_builder_mongodb_id_add_ingredient() with a Recipe object's mongodb_id and the fdc_id " \
                "of an ingredient to add to that recipe doesn't add the ingredient to the Recipe object"

    def test_recipes_builder_mongodb_id_add_ingredient_error_case_invalid_mongodb_id(self):
        bogus_mongodb_id = _generate_bogus_mongodb_id(Recipe)
        food_model_obj = random.choice(list(Food.objects.filter()))
        cgi_data = {"fdc_id": food_model_obj.fdc_id}
        request = self._middleware_and_user_bplate(
            self.request_factory.get(f"/recipes/builder/{bogus_mongodb_id}/add_ingredient/", data=cgi_data)
        )
        response = recipes_builder_mongodb_id_add_ingredient(request, bogus_mongodb_id)
        assert response.status_code == 404, "calling recipes_builder_mongodb_id_add_ingredient() with an " \
                "invalid objectid that doesn't correspond to any Recipe object doesn't yield a response with status code 404"
        content = response.content.decode('utf-8')
        error_message = "Error 404: no object in &#x27;recipes&#x27; collection in &#x27;nutritracker&#x27; data " \
                f"store with _id=&#x27;{bogus_mongodb_id}&#x27;"
        assert error_message in content, "calling recipes_builder_mongodb_id_add_ingredient() with an invalid " \
                "objectid that doesn't correspond to any Recipe object doesn't yield content containing the " \
                "appropriate error message"



