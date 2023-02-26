#!/usr/bin/python

import html
import faker

from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import authenticate, login
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from .models import Food, Ingredient, Recipe
from .views import recipes


food_model_argds = {
    'White Bread': {
        'energy_kcal': 280, 'fdc_id': 2131541, 'food_name': 'White Bread',
        'iron_mg': 3,  'protein_g': 8, 'serving_size': 25,
        'serving_units': 'g', 'sodium_mg': 540, 'sugars_g': 8,
        'total_carbohydrates_g': 52, 'total_fat_g': 2
    },
    'Whole Wheat Bread': {
        'calcium_mg': 47, 'dietary_fiber_g': 7, 'energy_kcal': 233,
        'fdc_id': 1886332, 'folate_B9_mcg': 19,
        'food_name': 'Whole Wheat Bread', 'iron_mg': 2, 'niacin_B3_mg': 2,
        'protein_g': 11, 'serving_size': 43, 'serving_units': 'g',
        'sodium_mg': 395, 'sugars_g': 6, 'total_carbohydrates_g': 44,
        'total_fat_g': 3
    },
    'Peanut Butter': {
        'calcium_mg': 49.0, 'dietary_fiber_g': 5.0, 'energy_kcal': 598.0,
        'fdc_id': 172470, 'folate_B9_mcg': 87.0, 'food_name': 'Peanut Butter',
        'iron_mg': 1.74, 'magnesium_mg': 168.0, 'niacin_B3_mg': 13.112,
        'pantothenic_acid_B5_mg': 1.137, 'phosphorous_mg': 335.0,
        'potassium_mg': 558.0, 'protein_g': 22.21, 'saturated_fat_g': 10.325,
        'serving_size': 1.0, 'serving_units': 'cup', 'sodium_mg': 17.0,
        'sugars_g': 10.49, 'total_carbohydrates_g': 22.31,
        'total_fat_g': 51.36, 'vitamin_E_mg': 9.1, 'zinc_mg': 2.51,
    },
    'Strawberry Jam': {
        'dietary_fiber_g': 1.0, 'energy_kcal': 37.0, 'fdc_id': 2009683,
        'food_name': 'Strawberry Jam', 'serving_size': 15.0,
        'serving_units': 'g', 'sodium_mg': 1.5, 'sugars_g': 8.0,
        'total_carbohydrates_g': 9.0
    },
    'Butter': {
         'cholesterol_mg': 30, 'energy_kcal': 100.0, 'fdc_id': 2094280,
         'food_name': 'Butter', 'protein_g': 1.0, 'saturated_fat_g': 7,
         'serving_size': 14.0, 'serving_units': 'g', 'sodium_mg': 95.1,
         'total_fat_g': 11.0
    },
    'Honey': {
        'calcium_mg': 6, 'energy_kcal': 304, 'fdc_id': 169640,
        'folate_B9_mcg': 2, 'food_name': 'Honey', 'magnesium_mg': 2,
        'phosphorous_mg': 4, 'potassium_mg': 52, 'serving_size': 1,
        'serving_units': 'cup', 'sodium_mg': 4, 'sugars_g': 82,
        'total_carbohydrates_g': 82
    },
}

recipe_ingredients = {
    'Peanut Butter & Jam Sandwich': {
        'White Bread': 3.04,
        'Peanut Butter': 0.1268025851,
        'Strawberry Jam': 2.626666667
    },
    'Peanut Butter Sandwich': {
        'Whole Wheat Bread': 2,
        'Peanut Butter': 0.1268025851
    },
    'Peanut Butter & Butter Sandwich': {
        'White Bread': 3.04,
        'Peanut Butter': 0.1268025851,
        'Strawberry Jam': 2.626666667,
        'Butter': 4
    },
    'Peanut Butter & Honey Sandwich': {
        'White Bread': 3.04,
        'Peanut Butter': 0.1268025851,
        'Honey': 0.04226752838
    }
}


class recipes_test_case(TestCase):

    def setUp(self):
        self.faker_obj = faker.Faker()
        self.test_username = self.faker_obj.user_name()
        self.test_password = self.faker_obj.password()
        self.test_user = User.objects.create_user(username=self.test_username, password=self.test_password)
        self.test_user.save()
        self.foods = dict()
        for food_name, food_model_argd in food_model_argds.items():
            food_model_obj = Food(**food_model_argd)
            food_model_obj.save()
            self.foods[food_name] = food_model_obj
        self.recipes = dict()
        for recipe_name, food_names_to_servings_numbers in recipe_ingredients.items():
            recipe_model_obj = Recipe(owner=self.test_username, recipe_name=recipe_name, complete=False, ingredients=list())
            for food_name, servings_number in food_names_to_servings_numbers.items():
                food_model_obj = self.foods[food_name]
                ingredient_model_obj = Ingredient(servings_number=servings_number, food=food_model_obj.serialize())
                ingredient_model_obj.save()
                recipe_model_obj.ingredients.append(ingredient_model_obj.serialize())
            recipe_model_obj.complete = True
            recipe_model_obj.save()
            self.recipes[recipe_name] = recipe_model_obj
        self.request_factory = RequestFactory()

    def tearDown(self):
        pass


class test_recipes(recipes_test_case):

    def test_recipes_normal_case(self):
        request = self.request_factory.get("/recipes/")
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        request.user = authenticate(username=self.test_username, password=self.test_password)
        login(request, request.user)
        content = recipes(request).content.decode('utf-8')
        for recipe_name in self.recipes.keys():
            recipe_name_esc = html.escape(recipe_name)
            assert recipe_name_esc in content, 'calling recipes(request) does not yield content containing the ' \
                    f'"recipe name "{recipe_name}" although it is in the data store and should be listed'
