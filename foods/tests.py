#!/usr/bin/python

import html
import random
import re
import urllib.parse
import json

from django.test.client import RequestFactory
from django.test import TestCase

from .models import Food
from .views import foods, foods_fdc_id, foods_local_search, foods_local_search_results
from utils import Food_Stub


food_params_to_nutrient_names = \
    dict(biotin_B7_mcg="Biotin (B7)", calcium_mg="Calcium", cholesterol_mg="Cholesterol", copper_mg="Copper",
         dietary_fiber_g="Dietary Fiber", energy_kcal="Calories", folate_B9_mcg="Folate (B9)", iodine_mcg="Iodine",
         iron_mg="Iron", magnesium_mg="Magnesium", niacin_B3_mg="Niacin (B3)",
         pantothenic_acid_B5_mg="Pantothenic Acid (B5)", phosphorous_mg="Phosphorous", potassium_mg="Potassium",
         protein_g="Protein", riboflavin_B2_mg="Riboflavin (B2)", saturated_fat_g="Saturated Fat", sodium_mg="Sodium",
         sugars_g="Sugars", thiamin_B1_mg="Thiamin (B1)", total_carbohydrates_g="Total Carbohydrates",
         total_fat_g="Total Fat", trans_fat_g="Trans Fat", vitamin_D_mcg="Vitamin D", vitamin_E_mg="Vitamin E",
         zinc_mg="Zinc")

food_params_to_units = \
    dict(biotin_B7_mcg="mcg", calcium_mg="mg", cholesterol_mg="mg", copper_mg="mg", dietary_fiber_g="g",
         energy_kcal="kcal", folate_B9_mcg="mcg", iodine_mcg="mcg", iron_mg="mg", magnesium_mg="mg", niacin_B3_mg="mg",
         pantothenic_acid_B5_mg="mg", phosphorous_mg="mg", potassium_mg="mg", protein_g="g", riboflavin_B2_mg="mg",
         saturated_fat_g="g", sodium_mg="mg", sugars_g="g", thiamin_B1_mg="mg", total_carbohydrates_g="g",
         total_fat_g="g", trans_fat_g="g", vitamin_D_mcg="mcg", vitamin_E_mg="mg", zinc_mg="mg")

food_model_objs_argds = [
    dict(biotin_B7_mcg=0, calcium_mg=0, cholesterol_mg=54, copper_mg=0, dietary_fiber_g=0, energy_kcal=125,
         fdc_id=2103038, folate_B9_mcg=0, food_name='Angus Roasted Beef', iodine_mcg=0, iron_mg=1, magnesium_mg=0,
         niacin_B3_mg=0, pantothenic_acid_B5_mg=0, phosphorous_mg=0, potassium_mg=0, protein_g=23, riboflavin_B2_mg=0,
         saturated_fat_g=0, serving_size=56, serving_units='g', sodium_mg=571, sugars_g=0, thiamin_B1_mg=0,
         total_carbohydrates_g=0, total_fat_g=3, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=64, cholesterol_mg=48, copper_mg=0, dietary_fiber_g=1, energy_kcal=287,
         fdc_id=2103039, folate_B9_mcg=0, food_name='Cornbread', iodine_mcg=0, iron_mg=1, magnesium_mg=0, niacin_B3_mg=0,
         pantothenic_acid_B5_mg=0, phosphorous_mg=0, potassium_mg=0, protein_g=4, riboflavin_B2_mg=0, saturated_fat_g=2,
         serving_size=94, serving_units='g', sodium_mg=500, sugars_g=20, thiamin_B1_mg=0, total_carbohydrates_g=52,
         total_fat_g=7, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=6, cholesterol_mg=0, copper_mg=0, dietary_fiber_g=0, energy_kcal=304, fdc_id=169640,
         folate_B9_mcg=2, food_name='Honey', iodine_mcg=0, iron_mg=0, magnesium_mg=2, niacin_B3_mg=0,
         pantothenic_acid_B5_mg=0, phosphorous_mg=4, potassium_mg=52, protein_g=0, riboflavin_B2_mg=0, saturated_fat_g=0,
         serving_size=1, serving_units='cup', sodium_mg=4, sugars_g=82, thiamin_B1_mg=0, total_carbohydrates_g=82,
         total_fat_g=0, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=123, cholesterol_mg=14, copper_mg=0, dietary_fiber_g=4, energy_kcal=198,
         fdc_id=1944909, folate_B9_mcg=0, food_name='Artisan Smooth & Creamy Gelato, Toasted Coconut', iodine_mcg=0,
         iron_mg=0, magnesium_mg=0, niacin_B3_mg=0, pantothenic_acid_B5_mg=0, phosphorous_mg=0, potassium_mg=170,
         protein_g=4, riboflavin_B2_mg=0, saturated_fat_g=8, serving_size=106, serving_units='g', sodium_mg=52,
         sugars_g=21, thiamin_B1_mg=0, total_carbohydrates_g=25, total_fat_g=10, trans_fat_g=0, vitamin_D_mcg=0,
         vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=138, cholesterol_mg=15, copper_mg=0, dietary_fiber_g=0, energy_kcal=71,
         fdc_id=1970473, folate_B9_mcg=0, food_name='Milk', iodine_mcg=0, iron_mg=0, magnesium_mg=0, niacin_B3_mg=0,
         pantothenic_acid_B5_mg=0, phosphorous_mg=104, potassium_mg=179, protein_g=3, riboflavin_B2_mg=0,
         saturated_fat_g=2, serving_size=240, serving_units='ml', sodium_mg=58, sugars_g=5, thiamin_B1_mg=0,
         total_carbohydrates_g=5, total_fat_g=3, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=0, cholesterol_mg=0, dietary_fiber_g=0, energy_kcal=0, fdc_id=2031685,
         folate_B9_mcg=0, food_name='Rooibos Caffeine-Free Red Tea Bags, Rooibos', iodine_mcg=0, iron_mg=0,
         magnesium_mg=0, niacin_B3_mg=0, pantothenic_acid_B5_mg=0, phosphorous_mg=0, potassium_mg=0, protein_g=0,
         riboflavin_B2_mg=0, saturated_fat_g=0, serving_size=2, serving_units='g', sodium_mg=0, sugars_g=0,
         thiamin_B1_mg=0, total_carbohydrates_g=0, total_fat_g=0, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0,
         zinc_mg=0, copper_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=0, cholesterol_mg=0, dietary_fiber_g=0, energy_kcal=0, fdc_id=946384,
         folate_B9_mcg=0, food_name='Splenda, No Calorie Granulated Sweetner', iodine_mcg=0, iron_mg=0, magnesium_mg=0,
         niacin_B3_mg=0, pantothenic_acid_B5_mg=0, phosphorous_mg=0, potassium_mg=0, protein_g=0, riboflavin_B2_mg=0,
         saturated_fat_g=0, serving_size=0.5, serving_units='g', sodium_mg=0, sugars_g=0, thiamin_B1_mg=0,
         total_carbohydrates_g=200, total_fat_g=0, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0, zinc_mg=0,
         copper_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=47, cholesterol_mg=0, copper_mg=0, dietary_fiber_g=7, energy_kcal=233,
         fdc_id=1886332, folate_B9_mcg=19, food_name='Whole Wheat Bread', iodine_mcg=0, iron_mg=2, magnesium_mg=0,
         niacin_B3_mg=2, pantothenic_acid_B5_mg=0, phosphorous_mg=0, potassium_mg=0, protein_g=11, riboflavin_B2_mg=0,
         saturated_fat_g=0, serving_size=43, serving_units='g', sodium_mg=395, sugars_g=6, thiamin_B1_mg=0,
         total_carbohydrates_g=44, total_fat_g=3, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=0, cholesterol_mg=0, copper_mg=0, dietary_fiber_g=0, energy_kcal=280,
         fdc_id=2131541, folate_B9_mcg=0, food_name='White Bread', iodine_mcg=0, iron_mg=3, magnesium_mg=0,
         niacin_B3_mg=0, pantothenic_acid_B5_mg=0, phosphorous_mg=0, potassium_mg=0, protein_g=8, riboflavin_B2_mg=0,
         saturated_fat_g=0, serving_size=25, serving_units='g', sodium_mg=540, sugars_g=8, thiamin_B1_mg=0,
         total_carbohydrates_g=52, total_fat_g=2, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=1, cholesterol_mg=0, copper_mg=0, dietary_fiber_g=0, energy_kcal=387, fdc_id=169655,
         folate_B9_mcg=0, food_name='Sugars, Granulated', iodine_mcg=0, iron_mg=0, magnesium_mg=0, niacin_B3_mg=0,
         pantothenic_acid_B5_mg=0, phosphorous_mg=0, potassium_mg=2, protein_g=0, riboflavin_B2_mg=0, saturated_fat_g=0,
         serving_size=1, serving_units='cup', sodium_mg=1, sugars_g=99, thiamin_B1_mg=0, total_carbohydrates_g=99,
         total_fat_g=0, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=15, cholesterol_mg=0, copper_mg=0, dietary_fiber_g=2, energy_kcal=364,
         fdc_id=169761, folate_B9_mcg=26, food_name='Wheat Flour, White, All-Purpose, Unenriched', iodine_mcg=0,
         iron_mg=1, magnesium_mg=22, niacin_B3_mg=1, pantothenic_acid_B5_mg=0, phosphorous_mg=108, potassium_mg=107,
         protein_g=10, riboflavin_B2_mg=0, saturated_fat_g=0, serving_size=1, serving_units='cup', sodium_mg=2,
         sugars_g=0, thiamin_B1_mg=0, total_carbohydrates_g=76, total_fat_g=0, trans_fat_g=0, vitamin_D_mcg=0,
         vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=0, cholesterol_mg=0, copper_mg=0, dietary_fiber_g=0, energy_kcal=0, fdc_id=175040,
         folate_B9_mcg=0, food_name='Leavening Agents, Baking Soda', iodine_mcg=0, iron_mg=0, magnesium_mg=0,
         niacin_B3_mg=0, pantothenic_acid_B5_mg=0, phosphorous_mg=0, potassium_mg=0, protein_g=0, riboflavin_B2_mg=0,
         saturated_fat_g=0, serving_size=0.5, serving_units='tsp', sodium_mg=27360, sugars_g=0, thiamin_B1_mg=0,
         total_carbohydrates_g=0, total_fat_g=0, trans_fat_g=0, vitamin_D_mcg=0, vitamin_E_mg=0, zinc_mg=0),
    dict(biotin_B7_mcg=0, calcium_mg=4332, cholesterol_mg=0, copper_mg=0, dietary_fiber_g=2, energy_kcal=97,
         fdc_id=172805, folate_B9_mcg=0, food_name='Leavening Agents, Baking Powder, Low-Sodium', iodine_mcg=0,
         iron_mg=8, magnesium_mg=29, niacin_B3_mg=0, pantothenic_acid_B5_mg=0, phosphorous_mg=6869, potassium_mg=10100,
         protein_g=0, riboflavin_B2_mg=0, saturated_fat_g=0, serving_size=0.5, serving_units='tsp', sodium_mg=90,
         sugars_g=0, thiamin_B1_mg=0, total_carbohydrates_g=46, total_fat_g=0, trans_fat_g=0, vitamin_D_mcg=0,
         vitamin_E_mg=0, zinc_mg=0)
]


class Mock_Fdc_Api_Contacter:

    with open("./test/mock_api_query_results.json", "r") as mock_api_json:
        search_results_prefetched_json = mock_api_json.read()
        search_results_parsed_json = json.loads(search_results_prefetched_json)

    def __init__(self, unneeded_api_key):
        pass

    def number_of_search_results(self, query):
        return len(self.search_results_parsed_json['foods'])

    def search_by_keywords(self, query, page_size=25, page_number=1):
        results_list = list()
        for result_obj in self.search_results_parsed_json['foods']:
            results_list.append(Food_Stub.from_fdc_json_obj(result_obj))
        return results_list


class foods_test_case(TestCase):

    def setUp(self):
        self.food_names = list()
        for food_argd in food_model_objs_argds:
            food_model_obj = Food(**food_argd)
            food_model_obj.save()
            self.food_names.append(html.escape(food_model_obj.food_name, quote=True))
        self.food_names.sort()
        self.request_factory = RequestFactory()

    def tearDown(self):
        for food_model_obj in Food.objects.filter():
            food_model_obj.delete()


class test_foods(foods_test_case):

    def test_foods_normal(self):
        request = self.request_factory.get("/foods/")
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

    def test_foods_pagination_normal(self):
        request = self.request_factory.get("/foods/", data={'page_number': 1, 'page_size': 10})
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

    def test_foods_pagination_error_bad_arg(self):
        request = self.request_factory.get("/foods/", data={'page_number': 'one', 'page_size': 10})
        content = foods(request).content.decode('utf-8')
        assert "value for page_number must be an integer; received &#x27;one&#x27;" in content, \
                "calling foods() with params {'page_number': 'one', 'page_size': 10} did not produce the correct error"

    def test_foods_pagination_error_overshooting_arg(self):
        request = self.request_factory.get("/foods/", data={'page_number': 3, 'page_size': 10})
        content = foods(request).content.decode('utf-8')
        assert "No more results" in content, \
                "calling foods() with params {'page_number': 3, 'page_size': 10} "\
                "did not produce 'No more results' message"


class test_foods_fdc_id(foods_test_case):

    def test_foods_fdc_id_normal(self):
        food_model_obj_argd = random.choice(food_model_objs_argds)
        fdc_id = food_model_obj_argd["fdc_id"]
        food_name = html.escape(food_model_obj_argd["food_name"])
        request = self.request_factory.get(f"/foods/{fdc_id}/")
        content = foods_fdc_id(request, fdc_id).content.decode('utf-8')
        assert food_name in content, f"calling foods_fdc_id(request, fdc_id={fdc_id}) "\
                f"returned content that did not contain food_name value '{food_name}'"
        for food_param, nutrient_name in food_params_to_nutrient_names.items():
            nutrient_amount = re.escape(str(food_model_obj_argd[food_param]))
            nutrient_units = re.escape(food_params_to_units[food_param])
            nutrient_name = re.escape(nutrient_name)
            if food_param == "energy_kcal":
                assert re.search(f">{nutrient_name}<.*\n.*\n.*>{nutrient_amount}<", content), f"returned content from "\
                        f"foods_fdc_id(request, fdc_id={fdc_id}) does not contain 'Calories' followed 2 lines later "\
                        f"with '>{nutrient_amount}<'"
            else:
                assert re.search(f">{nutrient_name}<.*\n.*>{nutrient_amount}{nutrient_units}<", content), \
                        f"returned content from foods_fdc_id(request, fdc_id={fdc_id}) does not contain '{nutrient_name}' "\
                        f"followed on the next line by '>{nutrient_amount}{nutrient_units}<'"

    def test_foods_fdc_id_error_invalid_id(self):
        # The fdc ids found in food_model_objs_argds are roughly in the range
        # [2**17, 2**22] == [131072, 4194304]
        spurious_fdc_id = random.randint(2**17, 2**22)
        # Just in case by some chance the random fdc id actually occurs in the
        # stored argds
        while any(food_argd["fdc_id"] == spurious_fdc_id for food_argd in food_model_objs_argds):
            spurious_fdc_id = random.randint(2**17, 2**22)
        request = self.request_factory.get(f"/foods/{spurious_fdc_id}/")
        response = foods_fdc_id(request, spurious_fdc_id)
        content = response.content.decode('utf-8')
        assert response.status_code == 404, "returned content from calling foods_fdc_id() with an invalid fdc_id " \
                "doesn't return a response with status_code == 404"
        assert f"no object in 'foods' collection in 'nutritracker' data store with FDC ID {spurious_fdc_id}" in content, \
                "returned content from calling foods_fdc_id() with an invalid fdc_id doesn't return document with " \
                "correct error message"

    def test_foods_fdc_id_error_id_with_duplicate_objs(self):
        first_food_argd = random.choice(food_model_objs_argds)
        first_fdc_id = first_food_argd["fdc_id"]
        second_food_argd = random.choice(food_model_objs_argds)
        while second_food_argd is first_food_argd:
            second_food_argd = random.choice(food_model_objs_argds)
        second_fdc_id = second_food_argd["fdc_id"]
        second_food_model_obj = Food.objects.get(fdc_id=second_fdc_id)
        second_food_model_obj.fdc_id = first_fdc_id
        second_food_model_obj.save()
        request = self.request_factory.get(f"/foods/{first_fdc_id}/")
        response = foods_fdc_id(request, first_fdc_id)
        content = response.content.decode('utf-8')
        assert response.status_code == 500, "returned content from calling foods_fdc_id() with an fdc_id that occurs " \
                "twice in the data store doesn't return a response with status_code == 500"
        assert f"inconsistent state: multiple objects matching query for FDC ID {first_fdc_id}" in content, \
                "returned content from calling foods_fdc_id() with an fdc_id that occurs twice in the data store " \
                "doesn't return document with correct error message"


class test_foods_local_search(foods_test_case):

    # /foods/local_search/ is essentially a static page, so there's not much to
    # test, since this suite is not testing the structure of the templates. The
    # response is tested for existing and the suite moves on. This test is more
    # useful to catch if foods_local_search() has started throwing an exception.
    def test_foods_local_search_normal(self):
        request = self.request_factory.get("/foods/local_search/")
        response = foods(request)
        assert response.status_code == 200, \
                "returned content from calling foods_local_search() does not have status_code == 200"


class test_foods_local_search_results(foods_test_case):

    def test_foods_local_search_results_normal(self):
        cgi_data = {'search_query': 'Bread', 'page_number': 1, 'page_size': 25}
        request = self.request_factory.get("/foods/local_search_results/", data=cgi_data)
        content = foods(request).content.decode('utf-8')
        matching_food_names = [food_argd["food_name"] for food_argd in food_model_objs_argds if "Bread" in food_argd["food_name"]]
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        for food_name in matching_food_names:
            assert food_name in content, f"calling foods_local_search(request) with CGI params {cgi_query_string} " \
                    "doesn't return a page with all matching food_names listed"

    def test_foods_local_search_results_pagination_normal(self):
        cgi_data = {'search_query': 'Bread', 'page_number': 1, 'page_size': 1}
        request = self.request_factory.get("/foods/local_search_results/", data=cgi_data)
        content = foods_local_search_results(request).content.decode('utf-8')
        bread_re = re.compile("bread", re.I)
        matching_food_names = sorted([html.escape(food_argd["food_name"]) for food_argd in food_model_objs_argds
                                                                              if bread_re.search(food_argd["food_name"])])
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        assert matching_food_names[0] in content, f"calling foods_local_search(request) with CGI params " \
                f"{cgi_query_string} didn't return a page which doesn't return a page containing '{matching_food_names[0]}'"
        assert matching_food_names[1] not in content, f"calling foods_local_search(request) with CGI params " \
                f"{cgi_query_string} returned a page which contains '{matching_food_names[1]}'"
        assert '<a href="/foods/local_search_results/?page_size=1&page_number=2&search_query=Bread">2</a>' in content, \
                "output of foods.views.foods() with params " \
                f"{cgi_query_string} doesn't contain pagination link to page 2"

    def test_foods_local_search_results_pagination_too_far(self):
        cgi_data = {'search_query': 'Bread', 'page_number': 3, 'page_size': 2}
        request = self.request_factory.get("/foods/local_search_results/", data=cgi_data)
        content = foods_local_search_results(request).content.decode('utf-8')
        assert "No more results" in content, f"calling foods_local_search(request) with page_number and page_size " \
                "values that places the page off the end of the results didn't produce a page containing " \
                "'No more results'"

    def test_foods_local_search_results_error_no_matches(self):
        cgi_data = {'search_query': 'Rowrbazzle', 'page_number': 1, 'page_size': 1}
        request = self.request_factory.get("/foods/local_search_results/", data=cgi_data)
        content = foods_local_search_results(request).content.decode('utf-8')
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        assert "No matches" in content, f"calling foods_local_search(request) with a non-matching search_query " \
                "doesn't return a page containing 'No matches'"


class test_foods_fdc_search(foods_test_case):

    def test_foods_fdc_search_normal(self):
        request = self.request_factory.get("/foods/fdc_search/")
        response = foods(request)
        assert response.status_code == 200, \
                "returned content from calling foods_fdc_search() does not have status_code == 200"


#class test_foods_fdc_search_results(foods_test_case):
