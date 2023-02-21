#!/usr/bin/python

import html

from django.test.client import RequestFactory
from django.test import TestCase

from .models import Food
from .views import foods


food_model_objs_argds = [
    {"fdc_id": 2103038, "food_name": 'Angus Roasted Beef', "serving_size": 56, "serving_units": 'g', "energy_kcal": 125,
     "total_fat_g": 3, "saturated_fat_g": 0, "trans_fat_g": 0, "cholesterol_mg": 54, "sodium_mg": 571,
     "total_carbohydrates_g": 0, "dietary_fiber_g": 0, "sugars_g": 0, "protein_g": 23, "vitamin_D_mcg": 0,
     "potassium_mg": 0, "iron_mg": 1, "calcium_mg": 0, "vitamin_E_mg": 0, "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0,
     "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0, "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 0,
     "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0 },
    {"fdc_id": 2103039, "food_name": 'Cornbread', "serving_size": 94, "serving_units": 'g', "energy_kcal": 287,
     "total_fat_g": 7, "saturated_fat_g": 2, "trans_fat_g": 0, "cholesterol_mg": 48, "sodium_mg": 500,
     "total_carbohydrates_g": 52, "dietary_fiber_g": 1, "sugars_g": 20, "protein_g": 4, "vitamin_D_mcg": 0,
     "potassium_mg": 0, "iron_mg": 1, "calcium_mg": 64, "vitamin_E_mg": 0, "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0,
     "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0, "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 0,
     "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 169640, "food_name": 'Honey', "serving_size": 1, "serving_units": 'cup', "energy_kcal": 304,
     "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0, "cholesterol_mg": 0, "sodium_mg": 4,
     "total_carbohydrates_g": 82, "dietary_fiber_g": 0, "sugars_g": 82, "protein_g": 0, "vitamin_D_mcg": 0,
     "potassium_mg": 52, "iron_mg": 0, "calcium_mg": 6, "vitamin_E_mg": 0, "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0,
     "niacin_B3_mg": 0, "folate_B9_mcg": 2, "biotin_B7_mcg": 0, "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 4,
     "iodine_mcg": 0, "magnesium_mg": 2, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 1944909, "food_name": 'Artisan Smooth & Creamy Gelato, Toasted Coconut', "serving_size": 106,
     "serving_units": 'g', "energy_kcal": 198, "total_fat_g": 10, "saturated_fat_g": 8, "trans_fat_g": 0,
     "cholesterol_mg": 14, "sodium_mg": 52, "total_carbohydrates_g": 25, "dietary_fiber_g": 4, "sugars_g": 21,
     "protein_g": 4, "vitamin_D_mcg": 0, "potassium_mg": 170, "iron_mg": 0, "calcium_mg": 123, "vitamin_E_mg": 0,
     "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0, "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0,
     "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 0, "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 1970473, "food_name": 'Milk', "serving_size": 240, "serving_units": 'ml', "energy_kcal": 71,
     "total_fat_g": 3, "saturated_fat_g": 2, "trans_fat_g": 0, "cholesterol_mg": 15, "sodium_mg": 58,
     "total_carbohydrates_g": 5, "dietary_fiber_g": 0, "sugars_g": 5, "protein_g": 3, "vitamin_D_mcg": 0,
     "potassium_mg": 179, "iron_mg": 0, "calcium_mg": 138, "vitamin_E_mg": 0, "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0,
     "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0, "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 104,
     "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 2031685, "food_name": 'Rooibos Caffeine-Free Red Tea Bags, Rooibos', "serving_size": 2,
     "serving_units": 'g', "energy_kcal": 0, "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0,
     "cholesterol_mg": 0, "sodium_mg": 0, "total_carbohydrates_g": 0, "dietary_fiber_g": 0, "sugars_g": 0,
     "protein_g": 0, "vitamin_D_mcg": 0, "potassium_mg": 0, "iron_mg": 0, "calcium_mg": 0, "vitamin_E_mg": 0,
     "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0, "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0,
     "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 0, "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 946384, "food_name": 'Splenda, No Calorie Granulated Sweetner', "serving_size": 0.5, "serving_units": 'g',
     "energy_kcal": 0, "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0, "cholesterol_mg": 0, "sodium_mg": 0,
     "total_carbohydrates_g": 200, "dietary_fiber_g": 0, "sugars_g": 0, "protein_g": 0, "vitamin_D_mcg": 0,
     "potassium_mg": 0, "iron_mg": 0, "calcium_mg": 0, "vitamin_E_mg": 0, "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0,
     "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0, "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 0,
     "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 1886332, "food_name": 'Whole Wheat Bread', "serving_size": 43, "serving_units": 'g', "energy_kcal": 233,
     "total_fat_g": 3, "saturated_fat_g": 0, "trans_fat_g": 0, "cholesterol_mg": 0, "sodium_mg": 395,
     "total_carbohydrates_g": 44, "dietary_fiber_g": 7, "sugars_g": 6, "protein_g": 11, "vitamin_D_mcg": 0,
     "potassium_mg": 0, "iron_mg": 2, "calcium_mg": 47, "vitamin_E_mg": 0, "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0,
     "niacin_B3_mg": 2, "folate_B9_mcg": 19, "biotin_B7_mcg": 0, "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 0,
     "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 2131541, "food_name": 'White Bread', "serving_size": 25, "serving_units": 'g', "energy_kcal": 280,
     "total_fat_g": 2, "saturated_fat_g": 0, "trans_fat_g": 0, "cholesterol_mg": 0, "sodium_mg": 540,
     "total_carbohydrates_g": 52, "dietary_fiber_g": 0, "sugars_g": 8, "protein_g": 8, "vitamin_D_mcg": 0,
     "potassium_mg": 0, "iron_mg": 3, "calcium_mg": 0, "vitamin_E_mg": 0, "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0,
     "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0, "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 0,
     "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 169655, "food_name": 'Sugars, Granulated', "serving_size": 1, "serving_units": 'cup', "energy_kcal": 387,
     "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0, "cholesterol_mg": 0, "sodium_mg": 1,
     "total_carbohydrates_g": 99, "dietary_fiber_g": 0, "sugars_g": 99, "protein_g": 0, "vitamin_D_mcg": 0,
     "potassium_mg": 2, "iron_mg": 0, "calcium_mg": 1, "vitamin_E_mg": 0, "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0,
     "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0, "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 0,
     "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 169761, "food_name": 'Wheat Flour, White, All-Purpose, Unenriched', "serving_size": 1,
     "serving_units": 'cup', "energy_kcal": 364, "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0,
     "cholesterol_mg": 0, "sodium_mg": 2, "total_carbohydrates_g": 76, "dietary_fiber_g": 2, "sugars_g": 0,
     "protein_g": 10, "vitamin_D_mcg": 0, "potassium_mg": 107, "iron_mg": 1, "calcium_mg": 15, "vitamin_E_mg": 0,
     "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0, "niacin_B3_mg": 1, "folate_B9_mcg": 26, "biotin_B7_mcg": 0,
     "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 108, "iodine_mcg": 0, "magnesium_mg": 22, "zinc_mg": 0,
     "copper_mg": 0},
    {"fdc_id": 175040, "food_name": 'Leavening Agents, Baking Soda', "serving_size": 0.5, "serving_units": 'tsp',
     "energy_kcal": 0, "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0, "cholesterol_mg": 0, "sodium_mg": 27360,
     "total_carbohydrates_g": 0, "dietary_fiber_g": 0, "sugars_g": 0, "protein_g": 0, "vitamin_D_mcg": 0,
     "potassium_mg": 0, "iron_mg": 0, "calcium_mg": 0, "vitamin_E_mg": 0, "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0,
     "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0, "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 0,
     "iodine_mcg": 0, "magnesium_mg": 0, "zinc_mg": 0, "copper_mg": 0},
    {"fdc_id": 172805, "food_name": 'Leavening Agents, Baking Powder, Low-Sodium', "serving_size": 0.5,
     "serving_units": 'tsp', "energy_kcal": 97, "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0,
     "cholesterol_mg": 0, "sodium_mg": 90, "total_carbohydrates_g": 46, "dietary_fiber_g": 2, "sugars_g": 0,
     "protein_g": 0, "vitamin_D_mcg": 0, "potassium_mg": 10100, "iron_mg": 8, "calcium_mg": 4332, "vitamin_E_mg": 0,
     "thiamin_B1_mg": 0, "riboflavin_B2_mg": 0, "niacin_B3_mg": 0, "folate_B9_mcg": 0, "biotin_B7_mcg": 0,
     "pantothenic_acid_B5_mg": 0, "phosphorous_mg": 6869, "iodine_mcg": 0, "magnesium_mg": 29, "zinc_mg": 0,
     "copper_mg": 0}
]

request_factory = RequestFactory()


class test_foods(TestCase):

    def setUp(self):
        self.food_names = list()
        for food_argd in food_model_objs_argds:
            food_model_obj = Food(**food_argd)
            food_model_obj.save()
            self.food_names.append(html.escape(food_model_obj.food_name, quote=True))
        self.food_names.sort()

    def test_foods_normal(self):
        request = request_factory.get("/foods/")
        content = foods(request).content.decode('utf-8')
        indexes = list()
        for food_name in self.food_names:
            assert food_name in content, f"'{food_name}' not in output of foods.views.foods()"
            indexes.append(content.index(food_name))
        for i in range(1, len(indexes) - 1):
            assert indexes[i - 1] < indexes[i] < indexes[i + 1], \
                    "food names not sorted in output of foods.views.foods(): " \
                    f"'{food_name[indexes[i - 1]]}', '{food_name[indexes[i]]}', " \
                    f"'{food_name[indexes[i + 1]]}' disordered"

    def test_foods_pagination(self):
        request = request_factory.get("/foods/", data={'page_number': 1, 'page_size': 10})
        content = foods(request).content.decode('utf-8')
        for food_name in self.food_names[:10]:
            assert food_name in content, f"'{food_name}' not in output of foods.views.foods() "\
                                         f"with params {{'page_number': 1, 'page_size': 10}}"
        for food_name in self.food_names[10:]:
            assert food_name not in content, f"'{food_name}' in output of foods.views.foods() with "\
                                             f"params {{'page_number': 1, 'page_size': 10}}  when it "\
                                             "shouldn't be; pagination went wrong"
        assert '<a href="/foods/?page_size=10&page_number=2">2</a>' in content, \
               "output of foods.views.foods() with params {'page_number': 1, 'page_size': 10} "\
               "doesn't contain pagination link to page 2"

    def test_foods_pagination_bad_arg(self):
        request = request_factory.get("/foods/", data={'page_number': 'one', 'page_size': 10})
        content = foods(request).content.decode('utf-8')
        assert "value for page_number must be an integer; received &#x27;one&#x27;" in content, \
                "calling foods() with params {'page_number': 'one', 'page_size': 10} did not produce the correct error"

    def test_foods_pagination_overshooting_arg(self):
        request = request_factory.get("/foods/", data={'page_number': 3, 'page_size': 10})
        content = foods(request).content.decode('utf-8')
        assert "No more results" in content, \
                "calling foods() with params {'page_number': 3, 'page_size': 10} "\
                "did not produce 'No more results' message"

    def tearDown(self):
        for food_model_obj in Food.objects.filter():
            food_model_obj.delete()


