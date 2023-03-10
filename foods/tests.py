#!/usr/bin/python

import os
import html
import random
import re
import urllib.parse
import json

from django.test.client import RequestFactory
from django.test import TestCase, tag

from .models import Food
from .views import foods, foods_fdc_id, foods_local_search, foods_local_search_results, foods_fdc_search, \
        foods_fdc_search_results, foods_fdc_search_fdc_id, foods_fdc_import
from nutritracker.utils import Food_Stub, Food_Detailed


food_params_to_nutrient_names = {
    'biotin_B7_mcg': 'Biotin (B7)', 'calcium_mg': 'Calcium', 'cholesterol_mg': 'Cholesterol', 'copper_mg': 'Copper',
    'dietary_fiber_g': 'Dietary Fiber', 'energy_kcal': 'Calories', 'folate_B9_mcg': 'Folate (B9)',
    'iodine_mcg': 'Iodine', 'iron_mg': 'Iron', 'magnesium_mg': 'Magnesium', 'niacin_B3_mg': 'Niacin (B3)',
    'pantothenic_acid_B5_mg': 'Pantothenic Acid (B5)', 'phosphorous_mg': 'Phosphorous', 'potassium_mg': 'Potassium',
    'protein_g': 'Protein', 'riboflavin_B2_mg': 'Riboflavin (B2)', 'saturated_fat_g': 'Saturated Fat',
    'sodium_mg': 'Sodium', 'sugars_g': 'Sugars', 'thiamin_B1_mg': 'Thiamin (B1)',
    'total_carbohydrates_g': 'Total Carbohydrates', 'total_fat_g': 'Total Fat', 'trans_fat_g': 'Trans Fat',
    'vitamin_D_mcg': 'Vitamin D', 'vitamin_E_mg': 'Vitamin E', 'zinc_mg': 'Zinc'
}


food_params_to_units = {
    'biotin_B7_mcg': 'mcg', 'calcium_mg': 'mg', 'cholesterol_mg': 'mg', 'copper_mg': 'mg', 'dietary_fiber_g': 'g',
    'energy_kcal': 'kcal', 'folate_B9_mcg': 'mcg', 'iodine_mcg': 'mcg', 'iron_mg': 'mg', 'magnesium_mg': 'mg',
    'niacin_B3_mg': 'mg', 'pantothenic_acid_B5_mg': 'mg', 'phosphorous_mg': 'mg', 'potassium_mg': 'mg',
    'protein_g': 'g', 'riboflavin_B2_mg': 'mg', 'saturated_fat_g': 'g', 'sodium_mg': 'mg', 'sugars_g': 'g',
    'thiamin_B1_mg': 'mg', 'total_carbohydrates_g': 'g', 'total_fat_g': 'g', 'trans_fat_g': 'g', 'vitamin_D_mcg': 'mcg',
    'vitamin_E_mg': 'mg', 'zinc_mg': 'mg'
}

food_model_objs_argds = [
    {
        'cholesterol_mg': 54, 'energy_kcal': 125, 'fdc_id': 2103038, 'food_name': 'Angus Roasted Beef',
        'iron_mg': 1, 'protein_g': 23, 'serving_size': 56, 'serving_units': 'g', 'sodium_mg': 571,
        'total_fat_g': 3
    },
    {
        'calcium_mg': 64, 'cholesterol_mg': 48, 'dietary_fiber_g': 1, 'energy_kcal': 287, 'fdc_id': 2103039,
        'food_name': 'Cornbread', 'iron_mg': 1, 'protein_g': 4, 'saturated_fat_g': 2, 'serving_size': 94,
        'serving_units': 'g', 'sodium_mg': 500, 'sugars_g': 20, 'total_carbohydrates_g': 52, 'total_fat_g': 7
    },
    {
        'calcium_mg': 6, 'energy_kcal': 304, 'fdc_id': 169640, 'folate_B9_mcg': 2, 'food_name': 'Honey',
        'magnesium_mg': 2, 'phosphorous_mg': 4, 'potassium_mg': 52, 'serving_size': 1, 'serving_units': 'cup',
        'sodium_mg': 4, 'sugars_g': 82, 'total_carbohydrates_g': 82
    },
    {
        'calcium_mg': 123, 'cholesterol_mg': 14, 'dietary_fiber_g': 4, 'energy_kcal': 198, 'fdc_id': 1944909,
        'food_name': 'Artisan Smooth & Creamy Gelato, Toasted Coconut', 'potassium_mg': 170, 'protein_g': 4,
        'saturated_fat_g': 8, 'serving_size': 106, 'serving_units': 'g', 'sodium_mg': 52, 'sugars_g': 21,
        'total_carbohydrates_g': 25, 'total_fat_g': 10
    },
    {
        'calcium_mg': 138, 'cholesterol_mg': 15, 'energy_kcal': 71, 'fdc_id': 1970473, 'food_name': 'Milk',
        'phosphorous_mg': 104, 'potassium_mg': 179, 'protein_g': 3, 'saturated_fat_g': 2, 'serving_size': 240,
        'serving_units': 'ml', 'sodium_mg': 58, 'sugars_g': 5, 'total_carbohydrates_g': 5, 'total_fat_g': 3
    },
    {
        'fdc_id': 2031685, 'serving_size': 2, 'serving_units': 'g',
        'food_name': 'Rooibos Caffeine-Free Red Tea Bags, Rooibos'
    },
    {
        'fdc_id': 946384, 'serving_units': 'g', 'total_carbohydrates_g': 200,
        'food_name': 'Splenda, No Calorie Granulated Sweetner'
    },
    {
        'calcium_mg': 47, 'dietary_fiber_g': 7, 'energy_kcal': 233, 'fdc_id': 1886332, 'folate_B9_mcg': 19,
        'food_name': 'Whole Wheat Bread', 'iron_mg': 2, 'niacin_B3_mg': 2, 'protein_g': 11, 'serving_size': 43,
        'serving_units': 'g', 'sodium_mg': 395, 'sugars_g': 6, 'total_carbohydrates_g': 44, 'total_fat_g': 3
    },
    {
        'energy_kcal': 280, 'fdc_id': 2131541, 'food_name': 'White Bread', 'iron_mg': 3, 'protein_g': 8,
        'serving_size': 25, 'serving_units': 'g', 'sodium_mg': 540, 'sugars_g': 8, 'total_carbohydrates_g': 52,
        'total_fat_g': 2
    },
    {
        'calcium_mg': 1, 'energy_kcal': 387, 'fdc_id': 169655, 'food_name': 'Sugars, Granulated', 'potassium_mg': 2,
        'serving_size': 1, 'serving_units': 'cup', 'sodium_mg': 1, 'sugars_g': 99, 'total_carbohydrates_g': 99
    },
    {
        'calcium_mg': 15, 'dietary_fiber_g': 2, 'energy_kcal': 364, 'fdc_id': 169761, 'folate_B9_mcg': 26, 'iron_mg': 1,
        'magnesium_mg': 22, 'niacin_B3_mg': 1, 'phosphorous_mg': 108, 'potassium_mg': 107, 'protein_g': 10,
        'serving_size': 1, 'serving_units': 'cup', 'sodium_mg': 2, 'total_carbohydrates_g': 76,
        'food_name': 'Wheat Flour, White, All-Purpose, Unenriched'
    },
    {
        'fdc_id': 175040, 'food_name': 'Leavening Agents, Baking Soda', 'serving_units': 'tsp',
        'sodium_mg': 27360
    },
    {
        'calcium_mg': 4332, 'dietary_fiber_g': 2, 'energy_kcal': 97, 'fdc_id': 172805, 'iron_mg': 8, 'magnesium_mg': 29,
        'phosphorous_mg': 6869, 'potassium_mg': 10100, 'serving_units': 'tsp', 'sodium_mg': 90,
        'total_carbohydrates_g': 46, 'food_name': 'Leavening Agents, Baking Powder, Low-Sodium',
    }
]


class Mock_Fdc_Api_Contacter:

    with open("./testing_data/search_by_keywords.json", "r") as search_by_keywords_fh:
        search_by_keywords_data = json.loads(search_by_keywords_fh.read())

    with open("./testing_data/number_of_search_results.json", "r") as number_of_search_results_fh:
        number_of_search_results_data = json.loads(number_of_search_results_fh.read())

    look_up_fdc_id_data = dict()

    for filename in os.listdir("./testing_data/"):
        if not filename.startswith("look_up_fdc_id_"):
            continue
        fdc_id = int(filename.removeprefix("look_up_fdc_id_").removesuffix(".json"))
        with open(f"./testing_data/{filename}") as look_up_fdc_id_fh:
            look_up_fdc_id_data[fdc_id] = json.loads(look_up_fdc_id_fh.read())

    def __init__(self, unneeded_api_key):
        pass

    def number_of_search_results(self, query):
        return len(self.number_of_search_results_data['foods'])

    def search_by_keywords(self, query, page_size=25, page_number=1):
        results_list = list()
        for result_obj in self.search_by_keywords_data['foods']:
            results_list.append(Food_Stub.from_fdc_json_obj(result_obj))
        return results_list

    def look_up_fdc_id(self, fdc_id):
        if fdc_id not in self.look_up_fdc_id_data:
            return None
        json_data = self.look_up_fdc_id_data[fdc_id]
        if not Food_Detailed.is_usable_json_object(json_data):
            return False
        return Food_Detailed.from_fdc_json_obj(json_data)


@tag("foods")
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

    def test_foods_normal_case(self):
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

    def test_foods_pagination_normal_case(self):
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

    def test_foods_pagination_error_case_bad_arg(self):
        request = self.request_factory.get("/foods/", data={'page_number': 'one', 'page_size': 10})
        content = foods(request).content.decode('utf-8')
        assert "value for page_number must be an integer; received &#x27;one&#x27;" in content, \
                "calling foods() with params {'page_number': 'one', 'page_size': 10} did not produce the correct error"

    def test_foods_pagination_error_case_overshooting_arg(self):
        request = self.request_factory.get("/foods/", data={'page_number': 3, 'page_size': 10})
        content = foods(request).content.decode('utf-8')
        assert "No more results" in content, \
                "calling foods() with params {'page_number': 3, 'page_size': 10} "\
                "did not produce 'No more results' message"


class test_foods_fdc_id(foods_test_case):

    def test_foods_fdc_id_normal_case(self):
        food_model_obj_argd = random.choice(food_model_objs_argds)
        fdc_id = food_model_obj_argd["fdc_id"]
        food_name = html.escape(food_model_obj_argd["food_name"])
        request = self.request_factory.get(f"/foods/{fdc_id}/")
        content = foods_fdc_id(request, fdc_id).content.decode('utf-8')
        assert food_name in content, f"calling foods_fdc_id(request, fdc_id={fdc_id}) "\
                f"returned content that did not contain food_name value '{food_name}'"
        for food_param, nutrient_name in food_params_to_nutrient_names.items():
            nutrient_amount = re.escape(str(food_model_obj_argd.get(food_param, 0)))
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

    def test_foods_fdc_id_error_case_invalid_id(self):
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
        error_message = f"no object in &#x27;foods&#x27; collection in &#x27;nutritracker&#x27; data store with " \
                        f"FDC ID {spurious_fdc_id}"
        assert error_message in content, "returned content from calling foods_fdc_id() with an invalid fdc_id " \
                "doesn't return document with correct error message"

    def test_foods_fdc_id_error_case_id_with_duplicate_objs(self):
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
    def test_foods_local_search_normal_case(self):
        request = self.request_factory.get("/foods/local_search/")
        response = foods_local_search(request)
        assert response.status_code == 200, \
                "returned content from calling foods_local_search() does not have status_code == 200"


class test_foods_local_search_results(foods_test_case):

    def test_foods_local_search_results_normal_case(self):
        cgi_data = {'search_query': 'Bread', 'page_number': 1, 'page_size': 25}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self.request_factory.get("/foods/local_search_results/", data=cgi_data)
        content = foods(request).content.decode('utf-8')
        matching_food_names = [food_argd["food_name"] for food_argd in food_model_objs_argds if "Bread" in food_argd["food_name"]]
        for food_name in matching_food_names:
            assert food_name in content, f"calling foods_local_search(request) with CGI params {cgi_query_string} " \
                    "doesn't return a page with all matching food_names listed"

    def test_foods_local_search_results_pagination_normal_case(self):
        cgi_data = {'search_query': 'Bread', 'page_number': 1, 'page_size': 1}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self.request_factory.get("/foods/local_search_results/", data=cgi_data)
        content = foods_local_search_results(request).content.decode('utf-8')
        bread_re = re.compile("bread", re.I)
        matching_food_names = sorted([html.escape(food_argd["food_name"]) for food_argd in food_model_objs_argds
                                                                              if bread_re.search(food_argd["food_name"])])
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
        assert "No more results" in content, "calling foods_local_search(request) with page_number and page_size " \
                "values that places the page off the end of the results didn't produce a page containing " \
                "'No more results'"

    def test_foods_local_search_results_error_case_no_matches(self):
        cgi_data = {'search_query': 'Rowrbazzle', 'page_number': 1, 'page_size': 1}
        request = self.request_factory.get("/foods/local_search_results/", data=cgi_data)
        content = foods_local_search_results(request).content.decode('utf-8')
        assert "No matches" in content, "calling foods_local_search(request) with a non-matching search_query " \
                "doesn't return a page containing 'No matches'"


class test_foods_fdc_search(foods_test_case):

    def test_foods_fdc_search_normal_case(self):
        request = self.request_factory.get("/foods/fdc_search/")
        response = foods_fdc_search(request)
        assert response.status_code == 200, \
                "returned content from calling foods_fdc_search() does not have status_code == 200"


class test_foods_fdc_search_results(foods_test_case):

    result_food_to_calories = [
        ('Bread', 146), ('Bread', 357), ('Bread', 263), ('Bread', 196), ('Bread', 240), ('Bread', 263), ('Bread', 222),
        ('Bread', 306), ('Bread', 306), ('Bread', 269), ('Bread', 8600), ('Bread', 250), ('Bread', 250), ('Bread', 250),
        ('Bread', 255), ('Bread', 248), ('Bread', 222), ('Bread, Cheese', 408), ('Bread, Cinnamon', 253),
        ('Bread, Egg', 287), ('Bread, Italian', 259), ('Bread, Oatmeal', 269), ('Bread, Potato', 266),
        ('Bread, Pumpernickel', 250), ('Bread, Rye', 259)
    ]

    def test_foods_fdc_search_results_normal_case(self):
        cgi_data = {'search_query': 'Bread', 'page_number': 1, 'page_size': 25}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self.request_factory.get("/foods/fdc_search_results/", data=cgi_data)
        response = foods_fdc_search_results(request, fdc_api_contacter=Mock_Fdc_Api_Contacter)
        content = response.content.decode('utf-8')
        for food, calories in self.result_food_to_calories:
            food_calories_re = re.compile(f">{food}<.*\n.*Calories: {calories}")
            assert food_calories_re.search(content), \
                    f"calling foods_fdc_search_results(request, Mock_Fdc_Api_Contacter) with cgi args " \
                    f"{cgi_query_string} yielded content that doesn't contain '>{Food}<' followed by 'Calories: " \
                    f"{calories}' on the next line (which is in the response JSON)"
        assert '<a href="/foods/fdc_search_results/?page_size=25&page_number=2&search_query=Bread">2</a>' in content, \
                f"calling foods_fdc_search_results(request, Mock_Fdc_Api_Contacter) with cgi args {cgi_query_string} " \
                "yielded content that didn't contain pagination link to page 2"

    def test_foods_fdc_search_results_error_case_overshooting_arg(self):
        cgi_data = {'search_query': 'Bread', 'page_number': 5, 'page_size': 25}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self.request_factory.get("/foods/fdc_search_results/", data=cgi_data)
        response = foods_fdc_search_results(request, fdc_api_contacter=Mock_Fdc_Api_Contacter)
        content = response.content.decode('utf-8')
        assert "No more results" in content, \
                f"calling foods_fdc_search_results(request, Mock_Fdc_Api_Contacter) with cgi args {cgi_query_string} " \
                "yielded content that didn't contain 'No more results'"
        assert '<a href="/foods/fdc_search_results/?page_size=25&page_number=2&search_query=Bread">2</a>' in content, \
                f"calling foods_fdc_search_results(request, Mock_Fdc_Api_Contacter) with cgi args {cgi_query_string} " \
                "yielded content that didn't contain pagination link to page 2"


class test_foods_fdc_search_fdc_id(foods_test_case):

    def test_foods_fdc_search_fdc_id_normal_case(self):
        fdc_id = random.choice(list(Mock_Fdc_Api_Contacter.look_up_fdc_id_data))
        request = self.request_factory.get(f"/foods/fdc_search/{fdc_id}/")
        mock_api_contacter = Mock_Fdc_Api_Contacter(str(hex(random.randint(2**63, 2**64))))
        response = foods_fdc_search_fdc_id(request, fdc_id, fdc_api_contacter=Mock_Fdc_Api_Contacter)
        content = response.content.decode('utf-8')
        food_obj = mock_api_contacter.look_up_fdc_id(fdc_id)
        food_name = html.escape(food_obj.food_name)
        assert f">{food_name} - from FoodData Central data<" in content, \
                f"calling foods_fdc_search_fdc_id(request, {fdc_id}, fdc_api_contacter=Mock_Fdc_Api_Contacter) doesn't " \
                f"yield content containing the food_name value of food object with fdc_id={fdc_id}"
        for food_param, nutrient_name in food_params_to_nutrient_names.items():
            nutrient_amount = getattr(food_obj, food_param).amount
            nutrient_amount = round(nutrient_amount) if nutrient_amount == round(nutrient_amount) else round(nutrient_amount, 1)
            nutrient_units = re.escape(food_params_to_units[food_param])
            nutrient_name = re.escape(nutrient_name)
            if food_param == "energy_kcal":
                assert re.search(f">{nutrient_name}<.*\n.*\n.*>{nutrient_amount}<", content), \
                        f"calling foods_fdc_search_fdc_id(request, {fdc_id}, fdc_api_contacter=Mock_Fdc_Api_Contacter) doesn't " \
                        f"yield content containing 'Calories' followed 2 lines later with '>{nutrient_amount}<'"
            else:
                assert re.search(f">{nutrient_name}<.*\n.*>{nutrient_amount}{nutrient_units}<", content), \
                        f"calling foods_fdc_search_fdc_id(request, {fdc_id}, fdc_api_contacter=Mock_Fdc_Api_Contacter) doesn't " \
                        f"yield content containing '{nutrient_name}' followed on the next line by " \
                        f"'>{nutrient_amount}{nutrient_units}<'"

    def test_foods_fdc_search_fdc_id_error_case_nonexistent_fdc_id(self):
        spurious_fdc_id = random.randint(2**17, 2**22)
        while spurious_fdc_id in Mock_Fdc_Api_Contacter.look_up_fdc_id_data:
            spurious_fdc_id = random.randint(2**17, 2**22)
        request = self.request_factory.get(f"/foods/fdc_search/{spurious_fdc_id}/")
        response = foods_fdc_search_fdc_id(request, spurious_fdc_id, fdc_api_contacter=Mock_Fdc_Api_Contacter)
        content = response.content.decode('utf-8')
        assert response.status_code == 404, f"calling foods_fdc_search_fdc_id(request, {spurious_fdc_id}, " \
                f"fdc_api_contacter=Mock_Fdc_Api_Contacter), where {spurious_fdc_id} is an invalid FDC ID, " \
                "doesn't return a response with status code 404"
        assert f"No such FDC ID in the FoodData Central database: {spurious_fdc_id}" in content, \
                f"calling foods_fdc_search_fdc_id(request, {spurious_fdc_id}, " \
                f"fdc_api_contacter=Mock_Fdc_Api_Contacter), where {spurious_fdc_id} is an invalid FDC ID, " \
                "doesn't yield content containing the appropriate error message"

    def test_foods_fdc_search_fdc_id_error_case_unusable_json_data(self):
        fdc_id = random.choice(list(Mock_Fdc_Api_Contacter.look_up_fdc_id_data))
        description = Mock_Fdc_Api_Contacter.look_up_fdc_id_data[fdc_id]["description"]
        del Mock_Fdc_Api_Contacter.look_up_fdc_id_data[fdc_id]["description"]
        request = self.request_factory.get(f"/foods/fdc_search/{fdc_id}/")
        response = foods_fdc_search_fdc_id(request, fdc_id, fdc_api_contacter=Mock_Fdc_Api_Contacter)
        content = response.content.decode('utf-8')
        Mock_Fdc_Api_Contacter.look_up_fdc_id_data[fdc_id]["description"] = description
        assert response.status_code == 500, f"calling foods_fdc_search_fdc_id(request, {fdc_id}, " \
                f"fdc_api_contacter=Mock_Fdc_Api_Contacter), where {fdc_id} is associated with " \
                "unusable JSON data, doesn't return a response with status code 500"
        assert f"Internal error in rendering food with ID {fdc_id}" in content, \
                f"calling foods_fdc_search_fdc_id(request, {fdc_id}, " \
                f"fdc_api_contacter=Mock_Fdc_Api_Contacter), where {fdc_id} is associated with " \
                "unusable JSON data, doesn't return a response with status code 500"


class test_foods_fdc_import(foods_test_case):

    def test_foods_fdc_import_normal_case_imported(self):
        fdc_id = random.choice(list(Mock_Fdc_Api_Contacter.look_up_fdc_id_data))
        cgi_data = {'fdc_id': fdc_id}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self.request_factory.get("/foods/fdc_import/", data=cgi_data)
        response = foods_fdc_import(request, fdc_api_contacter=Mock_Fdc_Api_Contacter)
        content = response.content.decode('utf-8')
        success_message = f'<b>Imported.</b> You can now access this food locally at <a href="/foods/{fdc_id}/">'
        assert success_message in content, f"calling foods_fdc_import(request, " \
                f"fdc_api_contacter=Mock_Fdc_Api_Contacter) with CGI params {cgi_query_string} doesn't yield " \
                "content containing the appropriate success message"
        food_objs = Food.objects.filter(fdc_id=fdc_id)
        assert len(food_objs) == 1, f"calling foods_fdc_import(request, fdc_api_contacter=Mock_Fdc_Api_Contacter) " \
                f"with CGI params {cgi_query_string} returned the appropriate result, but didn't actually " \
                "import the data at that fdc_id into the nutritracker data store"

    def test_foods_fdc_import_error_case_invalid_fdc_id(self):
        fdc_id = -1
        cgi_data = {'fdc_id': fdc_id}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self.request_factory.get("/foods/fdc_import/", data=cgi_data)
        response = foods_fdc_import(request, fdc_api_contacter=Mock_Fdc_Api_Contacter)
        content = response.content.decode('utf-8')
        error_message = "value for fdc_id must be an integer greater than or equal to 1; received &#x27;-1&#x27;"
        assert error_message in content, f"calling foods_fdc_import(request, fdc_api_contacter=Mock_Fdc_Api_Contacter)"\
                f" with CGI params {cgi_query_string} doesn't yield content containing the appropriate error message"

    def test_foods_fdc_import_normal_case_not_imported(self):
        mock_api_contacter = Mock_Fdc_Api_Contacter(str(hex(random.randint(2**63, 2**64))))
        fdc_id = random.choice(list(Mock_Fdc_Api_Contacter.look_up_fdc_id_data))
        food_obj = mock_api_contacter.look_up_fdc_id(fdc_id)
        food_model_cls_argd = food_obj.to_model_cls_args()
        food_model_obj = Food(**food_model_cls_argd)
        food_model_obj.save()
        cgi_data = {'fdc_id': fdc_id}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self.request_factory.get("/foods/fdc_import/", data=cgi_data)
        response = foods_fdc_import(request, fdc_api_contacter=Mock_Fdc_Api_Contacter)
        content = response.content.decode('utf-8')
        success_message = '<b>Not imported.</b> A food with this FDC ID already exists in the local database. ' \
                "It's accessible at " + f'<a href="/foods/{fdc_id}/">'
        assert success_message in content, f"calling foods_fdc_import(request, " \
                f"fdc_api_contacter=Mock_Fdc_Api_Contacter) with CGI params {cgi_query_string} where that food " \
                "object is present in the database doesn't yield content containing the appropriate success message"

    def test_foods_fdc_import_error_case_api_responds_fdc_id_invalid(self):
        spurious_fdc_id = random.randint(2**17, 2**22)
        while spurious_fdc_id in Mock_Fdc_Api_Contacter.look_up_fdc_id_data:
            spurious_fdc_id = random.randint(2**17, 2**22)
        cgi_data = {'fdc_id': spurious_fdc_id}
        cgi_query_string = urllib.parse.urlencode(cgi_data)
        request = self.request_factory.get("/foods/fdc_import/", data=cgi_data)
        response = foods_fdc_import(request, fdc_api_contacter=Mock_Fdc_Api_Contacter)
        content = response.content.decode('utf-8')
        assert f"No such FDC ID in the FoodData Central database: {spurious_fdc_id}" in content, \
                "calling foods_fdc_import(request, fdc_api_contacter=Mock_Fdc_Api_Contacter) with CGI " \
                f"params {cgi_query_string} where {spurious_fdc_id} is not present in the mock api doesn't " \
                "yield content containing the appropriate error message"


#class test_foods_add_food(foods_test_case):
#
#    def test_foods_add_food_normal_case_no_cgi(self):
#        # /foods/add_food/ is a static page, and this test suite doesn't test
#        # template validity, so all that can be tested here is that a result is
#        # returned with status 200.
#        request = self.request_factory.get("/foods/add_food/")
#        response = foods_add_food(request)
#        assert response.status_code == 200, \
#                "returned content from calling foods_add_food() with no CGI params does not have status_code == 200"
#
#    def test_foods_add_food_normal_case_w_params(self):
#        cgi_data = random.choice(food_model_objs_argds).copy()
#        del cgi_data["fdc_id"]
#        request = self.request_factory.post("/foods/fdc_import/", data=cgi_data)
#        response = foods_fdc_import(request)
#        content = response.content.decode('utf-8')
#        success_message = f'<b>Imported.</b> You can now access this food locally at <a href="/foods/{fdc_id}/">'
