#!/usr/bin/python

import abc
import json
import re
import requests
import functools
import math
import urllib.parse

from django.shortcuts import redirect

from django.http import HttpResponse

from pymongo import MongoClient


get_cgi_params = lambda request: request.GET if request.method == "GET" else request.POST if request.method == "POST" else {}

slice_output_list_by_page = lambda output_list, page_size, current_page: output_list[page_size * (current_page - 1) : page_size * (current_page - 1) + page_size]


ACTIVITY_LEVELS_TABLE = {1: "Sedentary", 2: "Lightly active", 3: "Moderately active", 4: "Active", 5: "Very active"}

FEET_TO_METERS_CONVERSION_FACTOR = 0.304800609601

POUNDS_TO_KILOGRAMS_CONVERSION_FACTOR = 0.45359237

BMI_THRESHOLDS = ((0,    18.4,     "underweight"),
                  (18.5, 24.9,     "healthy"),
                  (25.0, 29.9,     "overweight"),
                  (30.0, math.inf, "obese"))


def retrieve_pagination_params(template, context, request, default_page_size=25, redir_url='', query=False):
    if query and not redir_url:
        raise Exception("in retrieve_pagination_params(), called with query=True but redir_url is null; "
                        "need a url to redirect to if retrieving 'search_query' param")
    cgi_params = get_cgi_params(request)
    return_dict = dict()
    if query:
        return_dict["search_query"] = cgi_params.get("search_query", '')
        if not return_dict["search_query"]:
            return redirect(redir_url)
    retval = cast_to_int(cgi_params.get("page_size", default_page_size), 'page_size', template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    return_dict["page_size"] = retval
    retval = cast_to_int(cgi_params.get("page_number", 1), 'page_number', template, context, request)
    if isinstance(retval, HttpResponse):
        return retval
    return_dict["page_number"] = retval
    return return_dict


def cast_to_int(strval, param_name, template, context, request):
    try:
        intval = int(strval)
        assert intval > 0
    except (ValueError, AssertionError):
        context["error"] = True
        context["message"] = f"Error 422: value for {param_name} must be an integer greater than zero"
        return HttpResponse(template.render(context, request), status=422)
    return intval


def get_db_handle(db_name, host, port, username, password):
    client = MongoClient(host=host, port=int(port), username=username, password=password)
    db_handle = client['nutritracker']
    return db_handle, client


def title_case(strval):
    is_unc_alnum_punct = lambda strval: re.match("^[A-Za-zÀ-ÿ0-9._'ʼ’]+$", strval)

    capitalize = lambda strval: re.sub("[A-Za-zÀ-ÿ]", lambda m: m.group(0).upper(), strval, count=1)

    title_case_lc_words = {"a", "an", "and", "as", "at", "but", "by", "even", "for", "from", "if", "in", "into", "'n",
                           "n'", "'n'", "ʼn", "nʼ", "ʼnʼ", "’n", "n’", "’n’", "nor", "now", "of", "off", "on", "or",
                           "out", "so", "than", "that", "the", "to", "top", "up", "upon", "w", "when", "with", "yet"}

    tokenizing_re = re.compile("(?<=[A-Za-zÀ-ÿ0-9._'ʼ’])(?=[^A-Za-zÀ-ÿ0-9._'ʼ’])"
                                   "|"
                               "(?<=[^A-Za-zÀ-ÿ0-9._'ʼ’])(?=[A-Za-zÀ-ÿ0-9._'ʼ’])")

    tokens = tokenizing_re.split(strval)

    output = list()
    first_alpha_token_index = -1
    last_alpha_token_index = len(tokens)

    # Sometimes a string will begin or end with a sequence of non-alphanumeric
    # characters (such as an ellipsis) that count as a token. The rule that the
    # first and last words in a string to be titlecased only applies to the
    # first and last _actual words_, not counting non-alphanumeric substrings,
    # so the indexes of the first and last actual words need to be found.
    for index, token in zip(range(len(tokens)), tokens):
        if is_unc_alnum_punct(token):
            first_alpha_token_index = index
            break
    for index, token in zip(range(len(tokens) - 1, -1, -1), reversed(tokens)):
        if is_unc_alnum_punct(token):
            last_alpha_token_index = index
            break

    for index in range(len(tokens)):
        token = tokens[index]
        if re.match(r"^([A-Za-zÀ-ÿ]\.){2,}$", token):
            token = token.upper()
        elif index == first_alpha_token_index or index == last_alpha_token_index:
            token = capitalize(token)
        elif token.lower() in title_case_lc_words:
            token = token.lower()
        elif re.match("^([à-ÿa-z'’ʼ]+)$", token):
            token = capitalize(token)
        output.append(token)

    return ''.join(output)


class Navigation_Links_Displayer:
    __slots__ = 'nav_hrefs_to_texts',

    def __init__(self, nav_hrefs_to_texts):
        self.nav_hrefs_to_texts = nav_hrefs_to_texts

    def href_list_wo_one_callable(self, href_to_exclude):
        if href_to_exclude not in self.nav_hrefs_to_texts:
            raise Exception(f"href {href_to_exclude} not among the hrefs in stored href mapping")
        return functools.partial(self.href_list_wo_one, href_to_exclude)

    def full_href_list_callable(self):
        return functools.partial(self.full_href_list)

    def full_href_list(self):
        return " • ".join(f'<a href="{nav_href}">{nav_link_text}</a>' for nav_href, nav_link_text in self.nav_hrefs_to_texts.items())

    def href_list_wo_one(self, href_to_exclude):
        return " • ".join(f'<a href="{nav_href}">{nav_link_text}</a>' if nav_href != href_to_exclude else nav_link_text
                          for nav_href, nav_link_text in self.nav_hrefs_to_texts.items())


class Recipe_Detailed:
    __slots__ = 'mongodb_id', 'recipe_name', 'ingredients', 'complete'

    # This class calls for 26 properties that all behave identically apart from
    # which symbol they query, so this class generalizes that repeated __get__()
    # method.
    class Summing_Property:
        __slots__ = 'symbol', 'memoized'

        def __init__(self, symbol):
            self.symbol = symbol
            self.memoized = None

        def __get__(self, instance, instancetype=None):
            if self.memoized is not None:
                return self.memoized
            nutrient_obj = Nutrient.from_symbol(self.symbol)
            if len(instance.ingredients):
                amount = 0
                for ingr_obj in instance.ingredients:
                    if not hasattr(ingr_obj.food, self.symbol):
                        continue
                    amount += ingr_obj.servings_number * getattr(ingr_obj.food, self.symbol).amount
                nutrient_obj.amount = amount
            self.memoized = nutrient_obj
            return nutrient_obj

        def __set__(self, instance):
            raise AttributeError(f"'{instance.__class__.__name__}' object attribute '{self.symbol}' is read-only")

        def __delete__(self, instance):
            raise AttributeError(f"'{instance.__class__.__name__}' object attribute '{self.symbol}' is read-only")

    def __init__(self, recipe_name, mongodb_id=None, ingredients=[], complete=False):
        self.mongodb_id = mongodb_id
        self.recipe_name = title_case(recipe_name.lower())
        self.complete = complete
        ingredient_list = list()
        for ingredient_obj in ingredients:
            if isinstance(ingredient_obj, dict):
                ingredient_list.append(Ingredient_Detailed.from_json_obj(ingredient_obj))
            elif isinstance(ingredient_obj, Ingredient_Detailed):
                ingredient_list.append(ingredient_obj)
            else:
                raise ValueError(f"Recipe_Detailed.__init__ unable to import ingredient object of type '{ingredient_obj.__class__.__name__}'")
        self.ingredients = [Ingredient_Detailed.from_json_obj(ingredient_obj) for ingredient_obj in ingredients]

    @classmethod
    def from_json_obj(self, recipe_json_obj):
        return self(recipe_name=recipe_json_obj["recipe_name"], complete=recipe_json_obj["complete"], mongodb_id=recipe_json_obj["_id"], ingredients=recipe_json_obj["ingredients"])

    @classmethod
    def from_model_obj(self, recipe_model_obj):
        return self(recipe_name=recipe_model_obj.recipe_name, complete=bool(recipe_model_obj.complete), mongodb_id=recipe_model_obj._id, ingredients=recipe_model_obj.ingredients)

    biotin_B7_mcg          = Summing_Property('biotin_B7_mcg')
    calcium_mg             = Summing_Property('calcium_mg')
    cholesterol_mg         = Summing_Property('cholesterol_mg')
    copper_mg              = Summing_Property('copper_mg')
    dietary_fiber_g        = Summing_Property('dietary_fiber_g')
    energy_kcal            = Summing_Property('energy_kcal')
    folate_B9_mcg          = Summing_Property('folate_B9_mcg')
    iodine_mcg             = Summing_Property('iodine_mcg')
    iron_mg                = Summing_Property('iron_mg')
    magnesium_mg           = Summing_Property('magnesium_mg')
    niacin_B3_mg           = Summing_Property('niacin_B3_mg')
    pantothenic_acid_B5_mg = Summing_Property('pantothenic_acid_B5_mg')
    phosphorous_mg         = Summing_Property('phosphorous_mg')
    potassium_mg           = Summing_Property('potassium_mg')
    protein_g              = Summing_Property('protein_g')
    riboflavin_B2_mg       = Summing_Property('riboflavin_B2_mg')
    saturated_fat_g        = Summing_Property('saturated_fat_g')
    sodium_mg              = Summing_Property('sodium_mg')
    sugars_g               = Summing_Property('sugars_g')
    thiamin_B1_mg          = Summing_Property('thiamin_B1_mg')
    total_carbohydrates_g  = Summing_Property('total_carbohydrates_g')
    total_fat_g            = Summing_Property('total_fat_g')
    trans_fat_g            = Summing_Property('trans_fat_g')
    vitamin_D_mcg          = Summing_Property('vitamin_D_mcg')
    vitamin_E_mg           = Summing_Property('vitamin_E_mg')
    zinc_mg                = Summing_Property('zinc_mg')


class Nutrient:
    __slots__ = ('name', 'units', 'fdc_code', 'amount', 'symbol')

    daily_values = {'biotin_B7_mcg': 30, 'calcium_mg': 1300, 'cholesterol_mg': 300, 'copper_mg': 0.9,
                    'dietary_fiber_g': 28, 'folate_B9_mcg': 400, 'iodine_mcg': 150, 'iron_mg': 18,
                    'magnesium_mg': 420, 'niacin_B3_mg': 16, 'pantothenic_acid_B5_mg': 5,
                    'phosphorous_mg': 1250, 'potassium_mg': 4700, 'protein_g': 50,
                    'riboflavin_B2_mg': 1.3, 'saturated_fat_g': 20, 'sodium_mg': 2300, 'sugars_g': 50,
                    'thiamin_B1_mg': 1.2, 'total_carbohydrates_g': 275, 'total_fat_g': 78,
                    'vitamin_D_mcg': 20, 'vitamin_E_mg': 15, 'zinc_mg': 11}

    nutrient_symbols_to_numbers = {'protein_g': 203, 'total_fat_g': 204, 'total_carbohydrates_g': 205,
                                   'energy_kcal': 208, 'sugars_g': 269, 'dietary_fiber_g': 291,
                                   'calcium_mg': 301, 'iron_mg': 303, 'magnesium_mg': 304,
                                   'phosphorous_mg': 305, 'potassium_mg': 306, 'sodium_mg': 307,
                                   'zinc_mg': 309, 'copper_mg': 312, 'iodine_mcg': 314,
                                   'vitamin_E_mg': 323, 'vitamin_D_mcg': 324, 'thiamin_B1_mg': 404,
                                   'riboflavin_B2_mg': 405, 'niacin_B3_mg': 406,
                                   'pantothenic_acid_B5_mg': 410, 'biotin_B7_mcg': 416,
                                   'folate_B9_mcg': 417, 'cholesterol_mg': 601, 'trans_fat_g': 605,
                                   'saturated_fat_g': 606}

    nutrient_argds = {
        203: {"name": "protein (g)", "units": "g", "fdc_code": 203, "symbol": 'protein_g'},
        204: {"name": "total fat (g)", "units": "g", "fdc_code": 204, "symbol": 'total_fat_g'},
        205: {"name": "total carbohydrates (g)", "units": "g", "fdc_code": 205, "symbol": 'total_carbohydrates_g'},
        208: {"name": "energy (kcal)", "units": "kcal", "fdc_code": 208, "symbol": 'energy_kcal'},
        269: {"name": "sugars (g)", "units": "g", "fdc_code": 269, "symbol": 'sugars_g'},
        291: {"name": "dietary fiber (g)", "units": "g", "fdc_code": 291, "symbol": 'dietary_fiber_g'},
        301: {"name": "calcium (mg)", "units": "mg", "fdc_code": 301, "symbol": 'calcium_mg'},
        303: {"name": "iron (mg)", "units": "mg", "fdc_code": 303, "symbol": 'iron_mg'},
        304: {"name": "magnesium (mg)", "units": "mg", "fdc_code": 304, "symbol": 'magnesium_mg'},
        305: {"name": "phosphorus (mg)", "units": "mg", "fdc_code": 305, "symbol": 'phosphorous_mg'},
        306: {"name": "potassium (mg)", "units": "mg", "fdc_code": 306, "symbol": 'potassium_mg'},
        307: {"name": "sodium (mg)", "units": "mg", "fdc_code": 307, "symbol": 'sodium_mg'},
        309: {"name": "zinc (mg)", "units": "mg", "fdc_code": 309, "symbol": 'zinc_mg'},
        312: {"name": "copper (mg)", "units": "mg", "fdc_code": 312, "symbol": 'copper_mg'},
        314: {"name": "iodine (mcg)", "units": "mcg", "fdc_code": 314, "symbol": 'iodine_mcg'},
        323: {"name": "vitamin E (mg)", "units": "mg", "fdc_code": 323, "symbol": 'vitamin_E_mg'},
        324: {"name": "vitamin D (mcg)", "units": "mcg", "fdc_code": 324, "symbol": 'vitamin_D_mcg'},
        404: {"name": "thiamin (vitamin B1) (mg)", "units": "mg", "fdc_code": 404, "symbol": 'thiamin_B1_mg'},
        405: {"name": "riboflavin (vitamin B2) (mg)", "units": "mg", "fdc_code": 405, "symbol": 'riboflavin_B2_mg'},
        406: {"name": "niacin (vitamin B3) (mg)", "units": "mg", "fdc_code": 406, "symbol": 'niacin_B3_mg'},
        410: {"name": "pantothenic acid (mg)", "units": "mg", "fdc_code": 410, "symbol": 'pantothenic_acid_B5_mg'},
        416: {"name": "biotin (mcg)", "units": "mcg", "fdc_code": 416, "symbol": 'biotin_B7_mcg'},
        417: {"name": "folate (mcg)", "units": "mcg", "fdc_code": 417, "symbol": 'folate_B9_mcg'},
        601: {"name": "cholesterol (mg)", "units": "mg", "fdc_code": 601, "symbol": 'cholesterol_mg'},
        605: {"name": "trans fat (g)", "units": "g", "fdc_code": 605, "symbol": 'trans_fat_g'},
        606: {"name": "saturated fat (g)", "units": "g", "fdc_code": 606, "symbol": 'saturated_fat_g'},
    }

    def __init__(self, name, units, fdc_code=0, amount=0, symbol=''):
        self.name = name
        self.units = units
        self.fdc_code = fdc_code
        self.amount = amount
        self.symbol = symbol

    @classmethod
    def from_symbol(self, symbol):
        return self(**self.nutrient_argds[self.nutrient_symbols_to_numbers[symbol]])

    @property
    def dv_perc(self):
        if self.symbol not in self.daily_values:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute 'dv_perc'")
        if self.amount == 0:
            return 0
        else:
            return round(100 * self.amount / self.daily_values[self.symbol], 0)

    def copy(self):
        return Nutrient(self.name, self.units, fdc_code=self.fdc_code, amount=self.amount, symbol=self.symbol)

    def serialize(self):
        serialized = {'name': self.name,
                      'units': self.units,
                      'fdc_code': self.fdc_code,
                      'amount': self.amount,
                      'symbol': self.symbol}
        if hasattr(self, 'dv_perc'):
            serialized['dv_perc'] = self.dv_perc
        return serialized


class Abstract_Food(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def serialize(self):
        pass

    @classmethod
    @abc.abstractmethod
    def from_fdc_json_obj(self, json_obj):
        pass


class Food_Stub(Abstract_Food):
    __slots__ = ('fdc_id', 'food_name', 'calories', 'in_db_already')

    def __init__(self, fdc_id, food_name):
        self.fdc_id = fdc_id
        self.food_name = title_case(food_name.lower())
        self.in_db_already = False

    @classmethod
    def from_fdc_json_obj(self, food_json_obj):
        fdc_id = food_json_obj["fdcId"]
        food_name = food_json_obj["description"]
        food_obj = Food_Stub(fdc_id, food_name)
        for nutrient_json_obj in food_json_obj["foodNutrients"]:
            if int(nutrient_json_obj["nutrientNumber"]) != 208:
                continue
            food_obj.calories = float(nutrient_json_obj["value"])
            break
        if not hasattr(food_obj, 'calories'):
            food_obj.calories = None
        return food_obj

    def serialize(self):
        return {'fdc_id': self.fdc_id, 'food_name': self.food_name, 'calories': self.calories}


class Ingredient_Detailed:
    __slots__ = 'servings_number', 'food'

    def __init__(self, servings_number, food):
        self.servings_number = servings_number
        if hasattr(food, 'serialize'):
            food = food.serialize()
        self.food = Food_Detailed.from_nt_json_obj(food)

    @classmethod
    def from_json_obj(self, ingredient_json_obj):
        return self(servings_number=ingredient_json_obj["servings_number"], food=ingredient_json_obj["food"])

    @classmethod
    def from_model_obj(self, ingredient_model_obj):
        return self(servings_number=ingredient_model_obj.servings_number, food=ingredient_model_obj.food.serialize())


class Food_Detailed(Abstract_Food):
    __slots__ = ('fdc_id', 'food_name', 'serving_size', 'serving_units', 'in_db_already', 'biotin_B7_mcg', 'calcium_mg',
                 'cholesterol_mg', 'copper_mg', 'dietary_fiber_g', 'energy_kcal', 'folate_B9_mcg', 'iodine_mcg',
                 'iron_mg', 'magnesium_mg', 'niacin_B3_mg', 'pantothenic_acid_B5_mg', 'phosphorous_mg', 'potassium_mg',
                 'protein_g', 'riboflavin_B2_mg', 'saturated_fat_g', 'sodium_mg', 'sugars_g', 'thiamin_B1_mg',
                 'total_carbohydrates_g', 'total_fat_g', 'trans_fat_g', 'vitamin_D_mcg', 'vitamin_E_mg', 'zinc_mg')

    def __init__(self, fdc_id, food_name, serving_size, serving_units):
        self.fdc_id = fdc_id
        self.food_name = title_case(food_name.lower())
        self.serving_size = serving_size
        self.serving_units = serving_units
        for nutrient_argd in Nutrient.nutrient_argds.values():
            setattr(self, nutrient_argd['symbol'], None)
        self.in_db_already = False

    @classmethod
    def _food_json_obj_to_nutrient_table(self, food_json_obj):
        nutrient_table = dict()
        for nutrient_json_obj in food_json_obj["foodNutrients"]:
            fdc_code = int(nutrient_json_obj["nutrient"]["number"])
            if fdc_code not in Nutrient.nutrient_argds:
                continue
            elif "amount" not in nutrient_json_obj:
                continue
            nutrient_table[fdc_code] = Nutrient(nutrient_json_obj["nutrient"]["name"],
                                                nutrient_json_obj["nutrient"]["unitName"].lower(),
                                                fdc_code=fdc_code,
                                                amount=float(nutrient_json_obj["amount"]),
                                                symbol=Nutrient.nutrient_argds[fdc_code]["symbol"])
        return nutrient_table

    @classmethod
    def from_model_obj(self, food_model_obj):
        fdc_id = food_model_obj.fdc_id
        food_name = food_model_obj.food_name
        serving_size = food_model_obj.serving_size
        serving_units = food_model_obj.serving_units
        food_obj = self(fdc_id, food_name, serving_size, serving_units)
        for fdc_id, nutrient_argd in Nutrient.nutrient_argds.items():
            nutrient_in_food = Nutrient(**nutrient_argd)
            if hasattr(food_model_obj, nutrient_in_food.symbol):
                nutrient_in_food.amount = getattr(food_model_obj, nutrient_in_food.symbol)
            else:
                nutrient_in_food.amount = 0
            setattr(food_obj, nutrient_in_food.symbol, nutrient_in_food)
        return food_obj

    @classmethod
    def is_usable_json_object(self, food_json_obj):
        if food_json_obj["dataType"] == "SR Legacy":
            return ("fdcId" in food_json_obj and "description" in food_json_obj and "foodPortions" in food_json_obj
                    and len(food_json_obj["foodPortions"])
                    and "amount" in food_json_obj["foodPortions"][0] and "modifier" in food_json_obj["foodPortions"][0])
        elif food_json_obj["dataType"] == "Branded":
            return ("fdcId" in food_json_obj and "description" in food_json_obj
                    and "servingSize" in food_json_obj and "servingSizeUnit" in food_json_obj)

    @classmethod
    def from_fdc_json_obj(self, food_json_obj):
        fdc_id = food_json_obj["fdcId"]
        food_name = food_json_obj["description"]
        if food_json_obj["dataType"] == "SR Legacy":
            serving_size = food_json_obj["foodPortions"][0]["amount"]
            serving_units = food_json_obj["foodPortions"][0]["modifier"]
        elif food_json_obj["dataType"] == "Branded":
            serving_size = food_json_obj["servingSize"]
            serving_units = food_json_obj["servingSizeUnit"]
        else:
            raise Exception(f'while processing a food JSON object, unsupported value for property \'dataType\': {food_json_obj["dataType"]}')
        food_obj = self(fdc_id, food_name, serving_size, serving_units)
        nutrient_table = self._food_json_obj_to_nutrient_table(food_json_obj)
        for fdc_code, nutrient_argd in Nutrient.nutrient_argds.items():
            if fdc_code in nutrient_table:
                nutrient_in_food = nutrient_table[fdc_code]
                if nutrient_in_food.symbol == "vitamin_D_mcg" and nutrient_in_food.units.upper() == 'IU':
                    # The FDC uses IU for vitamin D, but this program stores vitamin
                    # D amounts in micrograms. Converting from IU to mg/mcg is
                    # different for every substance that IU are used with. For
                    # vitamin D, 40 IU == 1 mcg.
                    nutrient_in_food.amount /= 40
                    nutrient_in_food.units = 'mcg'
                setattr(food_obj, nutrient_argd["symbol"], nutrient_in_food)
            else:
                nutrient_in_food = Nutrient(**nutrient_argd)
                nutrient_in_food.amount = 0
                setattr(food_obj, nutrient_in_food.symbol, nutrient_in_food)
        return food_obj

    def to_nt_json_code(self):
        return json.dumps(self.serialize())

    @classmethod
    def from_nt_json_obj(self, json_content):
        const_args = {'fdc_id', 'food_name', 'serving_size', 'serving_units'}
        const_argd = {key: value for key, value in filter(lambda pair: pair[0] in const_args, json_content.items())}
        food_obj = self(**const_argd)
        for key, value in json_content.items():
            if key in const_args or key == '_id':
                continue
            if isinstance(value, dict):
                nutrient_argd = value.copy()
                if 'dv_perc' in nutrient_argd:
                    del nutrient_argd['dv_perc']
                nutrient_in_food = Nutrient(**nutrient_argd)
            else:
                nutrient_in_food = Nutrient(**Nutrient.nutrient_argds[Nutrient.nutrient_symbols_to_numbers[key]])
                nutrient_in_food.amount = value
            setattr(food_obj, key, nutrient_in_food)
        return food_obj

    def serialize(self):
        serialized = dict()
        for attr_name in self.__slots__:
            attr_val = getattr(self, attr_name)
            if attr_val == 0 or attr_val is None:
                continue
            if hasattr(attr_val, 'serialize'):
                serialized[attr_name] = attr_val.serialize()
            else:
                serialized[attr_name] = attr_val
        return serialized

    def to_model_cls_args(self):
        return {property_key: (property_val["amount"] if isinstance(property_val, dict) else property_val)
                for property_key, property_val in self.serialize().items()}


class Fdc_Api_Contacter:
    __slots__ = 'api_key',

    api_url = "https://api.nal.usda.gov/fdc/v1"

    get_fdc_lookup_url = lambda self, fdc_id: f"{self.api_url}/food/{fdc_id}?api_key={self.api_key}"

    get_fdc_search_url = lambda self: f"{self.api_url}/foods/search?api_key={self.api_key}"

    get_food_list_url = lambda self: f"{self.api_url}/foods/list?api_key={self.api_key}"

    def __init__(self, api_key):
        self.api_key = api_key

    def _keyword_search(self, query, page_size=None, page_number=None):
        search_url = self.get_fdc_search_url()
        json_argd = {'dataType': ["Branded", "SR Legacy"], 'query': query}
        if page_size is not None:
            json_argd['pageSize'] = page_size
        if page_number is not None:
            json_argd['pageNumber'] = page_number
        response = requests.post(search_url, json=json_argd)
        return json.loads(response.content)

    def search_by_keywords(self, query, page_size=25, page_number=1):
        json_content = self._keyword_search(query, page_size, page_number)
        results_list = list()
        for result_obj in json_content['foods']:
            results_list.append(Food_Stub.from_fdc_json_obj(result_obj))
        return results_list

    def number_of_search_results(self, query):
        return len(self._keyword_search(query)['foods'])

    def look_up_fdc_id(self, fdc_id):
        lookup_url = self.get_fdc_lookup_url(fdc_id)
        response = requests.get(lookup_url)
        if response.status_code == 404:
            return None
        json_content = json.loads(response.content)
        if not Food_Detailed.is_usable_json_object(json_content):
            return False
        return Food_Detailed.from_fdc_json_obj(json_content)

    def retrieve_foods_list(self, food_list_page=1):
        food_list_url = self.get_food_list_url()
        json_argd = dict(dataType=["Branded", "SR Legacy"])
        if food_list_page:
            json_argd["pageNumber"] = food_list_page
        response = requests.post(food_list_url, json=json_argd)
        results_list = list()
        for response_obj in json.loads(response.content):
            food_stub_obj = Food_Stub.from_fdc_json_obj(response_obj)
            results_list.append(food_stub_obj.serialize())
        return results_list


def generate_pagination_links(url_base, results_count, page_size, current_page, search_query=None):
    if results_count < page_size:
        return ''
    number_of_pages = math.ceil(results_count / page_size)
    page_links = list()
    for page_number in range(1, number_of_pages + 1):
        if page_number == current_page:
            page_links.append(str(page_number))
        else:
            url_params = {'page_size': page_size, 'page_number': page_number}
            if search_query is not None:
                url_params['search_query'] = search_query
            params = urllib.parse.urlencode(url_params)
            page_links.append(f'<a href="{url_base}?{params}">{page_number}</a>')
    return " • ".join(page_links)

