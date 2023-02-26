#!/usr/bin/python

import random
import html
import faker
import urllib.parse

from bson.objectid import ObjectId
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import authenticate, login, logout
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from .models import Food, Ingredient, Recipe
from .views import recipes, recipes_mongodb_id, recipes_search, recipes_search_results


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
        'White Bread': 3.04, 'Peanut Butter': 0.1268025851, 'Strawberry Jam': 2.626666667, 'Butter': 4
    },
    'Peanut Butter & Honey Sandwich': {
        'White Bread': 3.04, 'Peanut Butter': 0.1268025851, 'Honey': 0.04226752838
    }
}


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
        pass


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
        assert "No more results" in content, f"calling recipes(request) with cgi params {cgi_query_string} that " \
                "should point to a page off the end of the recipes list didn't yield content containing " \
                "appropriate error message"
        assert '<a href="/recipes/?page_size=2&page_number=2">2</a>' in content, f"calling recipes(request) with " \
                f"cgi params {cgi_query_string} that should point to a page off the end of the recipes list didn't " \
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
            assert recipe_name_esc in content, f'calling recipes(request) with cgi params {cgi_query_string} does ' \
                    f'not yield content containing the recipe name "{recipe_name}" although it is in the data store ' \
                    'and should be listed'
        for recipe_name in recipe_names[2:]:
            recipe_name_esc = html.escape(recipe_name)
            assert recipe_name_esc not in content, f'calling recipes(request) with cgi params {cgi_query_string} ' \
                    'yields content containing the recipe name "{recipe_name}" although the params should put ' \
                    'it on a later page'
        assert '<a href="/recipes/?page_size=2&page_number=2">2</a>' in content, "calling recipes(request) with " \
                f"cgi params {cgi_query_string} didn't yield content containing correct pagination links"

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
        # Those two very big integers are 0x100000000000000000000000 and 0xffffffffffffffffffffffff. The argument to
        # ObjectId must have 24 digits when displayed in hexadecimal to be taken as a valid object.
        bogus_mongodb_id = ObjectId(str(hex(random.randint(4951760157141521099596496896,
                                                          79228162514264337593543950335))).removeprefix("0x"))
        # Just in case by random chance a valid object id was picked.
        while len(Recipe.objects.filter(_id=bogus_mongodb_id)):
            bogus_mongodb_id = ObjectId(str(hex(random.randint(4951760157141521099596496896,
                                                              79228162514264337593543950335))).removeprefix("0x"))
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
                assert recipe_name_esc in content, f'calling recipes_search_results(request) with cgi params ' \
                        f'{cgi_query_string} does not yield content containing the recipe name "{recipe_name}" ' \
                        'although it is a match and should be listed'
            else:
                assert recipe_name_esc not in content, f'calling recipes_search_results(request) with cgi params ' \
                        f'{cgi_query_string} yields content containing the recipe name "{recipe_name}" although it ' \
                        'is not a match and should not be listed'
