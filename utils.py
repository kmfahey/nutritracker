#!/usr/bin/python

import abc
import decouple
import json
import re
import requests

from pymongo import MongoClient


def get_db_handle(db_name, host, port, username, password):
    client = MongoClient(host=host, port=int(port), username=username, password=password)
    db_handle = client['db_name']
    return db_handle, client


class Nutrient:
    __slots__ = ('name', 'units', 'fdc_code', 'amount', 'symbol')

    daily_values = {'biotin_mcg': 30, 'calcium_mg': 1300, 'cholesterol_mg': 300, 'copper_mg': 0.9,
                    'dietary_fiber_g': 28, 'folate_mcg': 400, 'iodine_mcg': 150, 'iron_mg': 18,
                    'magnesium_mg': 420, 'niacin_B3_mg': 16, 'pantothenic_acid_B5_mg': 5,
                    'phosphorous_mg': 1250, 'potassium_mg': 4700, 'protein_g': 50,
                    'riboflavin_B2_mg': 1.3, 'saturated_fat_g': 20, 'sodium_mg': 2300, 'sugars_g': 50,
                    'thiamin_B1_mg': 1.2, 'total_carbohydrates_g': 275, 'total_fat_g': 78,
                    'vitamin_D_mcg': 20, 'vitamin_E_mg': 15, 'zinc_mg': 11}

    def __init__(self, name, units, fdc_code=0, amount=0, symbol=''):
        self.name = name
        self.units = units
        self.fdc_code = fdc_code
        self.amount = amount
        self.symbol = symbol

    @property
    def dv_perc(self):
        if self.symbol not in self.daily_values:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute 'dv_perc'")
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

    nutrients = {
        203: Nutrient("protein (g)", "g", fdc_code=203, symbol='protein_g'),
        204: Nutrient("total fat (g)", "g", fdc_code=204, symbol='total_fat_g'),
        205: Nutrient("total carbohydrates (g)", "g", fdc_code=205, symbol='total_carbohydrates_g'),
        208: Nutrient("energy (kcal)", "kcal", fdc_code=208, symbol='energy_kcal'),
        269: Nutrient("sugars (g)", "g", fdc_code=269, symbol='sugars_g'),
        291: Nutrient("dietary fiber (g)", "g", fdc_code=291, symbol='dietary_fiber_g'),
        301: Nutrient("calcium (mg)", "mg", fdc_code=301, symbol='calcium_mg'),
        303: Nutrient("iron (mg)", "mg", fdc_code=303, symbol='iron_mg'),
        304: Nutrient("magnesium (mg)", "mg", fdc_code=304, symbol='magnesium_mg'),
        305: Nutrient("phosphorus (mg)", "mg", fdc_code=305, symbol='phosphorous_mg'),
        306: Nutrient("potassium (mg)", "mg", fdc_code=306, symbol='potassium_mg'),
        307: Nutrient("sodium (mg)", "mg", fdc_code=307, symbol='sodium_mg'),
        309: Nutrient("zinc (mg)", "mg", fdc_code=309, symbol='zinc_mg'),
        312: Nutrient("copper (mg)", "mg", fdc_code=312, symbol='copper_mg'),
        314: Nutrient("iodine (mcg)", "mcg", fdc_code=314, symbol='iodine_mcg'),
        323: Nutrient("vitamin E (mg)", "mg", fdc_code=323, symbol='vitamin_E_mg'),
        324: Nutrient("vitamin D (mcg)", "mcg", fdc_code=324, symbol='vitamin_D_mcg'),
        404: Nutrient("thiamin (vitamin B1) (mg)", "mg", fdc_code=404, symbol='thiamin_B1_mg'),
        405: Nutrient("riboflavin (vitamin B2) (mg)", "mg", fdc_code=405, symbol='riboflavin_B2_mg'),
        406: Nutrient("niacin (vitamin B3) (mg)", "mg", fdc_code=406, symbol='niacin_B3_mg'),
        410: Nutrient("pantothenic acid (mg)", "mg", fdc_code=410, symbol='pantothenic_acid_B5_mg'),
        416: Nutrient("biotin (mcg)", "mcg", fdc_code=416, symbol='biotin_mcg'),
        417: Nutrient("folate (mcg)", "mcg", fdc_code=417, symbol='folate_mcg'),
        601: Nutrient("cholesterol (mg)", "mg", fdc_code=601, symbol='cholesterol_mg'),
        605: Nutrient("trans fat (g)", "g", fdc_code=605, symbol='trans_fat_g'),
        606: Nutrient("saturated fat (g)", "g", fdc_code=606, symbol='saturated_fat_g'),
    }

    title_case_lc_words = {"a", "an", "and", "as", "at", "but", "by", "even", "for", "from", "if", "in", "into", "'n",
                           "n'", "'n'", "ʼn", "nʼ", "ʼnʼ", "’n", "n’", "’n’", "nor", "now", "of", "off", "on", "or",
                           "out", "so", "than", "that", "the", "to", "top", "up", "upon", "w", "when", "with", "yet"}

    tokenizing_re = re.compile("(?<=[A-Za-zÀ-ÿ0-9._'ʼ’])(?=[^A-Za-zÀ-ÿ0-9._'ʼ’])"
                                   "|"
                               "(?<=[^A-Za-zÀ-ÿ0-9._'ʼ’])(?=[A-Za-zÀ-ÿ0-9._'ʼ’])")

    _is_unc_alnum_punct = classmethod(lambda self, strval: re.match("^[A-Za-zÀ-ÿ0-9._'ʼ’]+$", strval))

    _capitalize = classmethod(lambda self, strval: re.sub("[A-Za-zÀ-ÿ]", lambda m: m.group(0).upper(), strval, count=1))

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def serialize(self):
        pass

    @classmethod
    @abc.abstractmethod
    def from_json_object(self, json_obj):
        pass

    @classmethod
    def _title_case(self, strval):

        tokens = self.tokenizing_re.split(strval)

        output = list()
        first_alpha_token_index = -1
        last_alpha_token_index = len(tokens)

        # Sometimes a string will begin or end with a sequence of non-alphanumeric
        # characters (such as an ellipsis) that count as a token. The rule that the
        # first and last words in a string to be titlecased only applies to the
        # first and last _actual words_, not counting non-alphanumeric substrings,
        # so the indexes of the first and last actual words need to be found.
        for index, token in zip(range(len(tokens)), tokens):
            if self._is_unc_alnum_punct(token):
                first_alpha_token_index = index
                break
        for index, token in zip(range(len(tokens) - 1, -1, -1), reversed(tokens)):
            if self._is_unc_alnum_punct(token):
                last_alpha_token_index = index
                break

        for index in range(len(tokens)):
            token = tokens[index]
            if re.match(r"^([A-Za-zÀ-ÿ]\.){2,}$", token):
                token = token.upper()
            elif index == first_alpha_token_index or index == last_alpha_token_index:
                token = self._capitalize(token)
            elif token.lower() in self.title_case_lc_words:
                token = token.lower()
            elif re.match("^([à-ÿa-z'’ʼ]+)$", token):
                token = self._capitalize(token)
            output.append(token)

        return ''.join(output)


class Food_Stub(Abstract_Food):
    __slots__ = ('fdc_id', 'food_name', 'calories')

    def __init__(self, fdc_id, food_name):
        self.fdc_id = fdc_id
        self.food_name = self._title_case(food_name)

    @classmethod
    def from_json_object(self, food_json_obj):
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


class Food_Detailed(Abstract_Food):
    __slots__ = ('fdc_id', 'food_name', 'serving_size', 'serving_units', 'biotin_mcg', 'calcium_mg', 'cholesterol_mg',
                 'copper_mg', 'dietary_fiber_g', 'energy_kcal', 'folate_mcg', 'iodine_mcg', 'iron_mg', 'magnesium_mg',
                 'niacin_B3_mg', 'pantothenic_acid_B5_mg', 'phosphorous_mg', 'potassium_mg', 'protein_g',
                 'riboflavin_B2_mg', 'saturated_fat_g', 'sodium_mg', 'sugars_g', 'thiamin_B1_mg',
                 'total_carbohydrates_g', 'total_fat_g', 'trans_fat_g', 'vitamin_D_mcg', 'vitamin_E_mg', 'zinc_mg')

    def __init__(self, fdc_id, food_name, serving_size, serving_units):
        self.fdc_id = fdc_id
        self.food_name = self._title_case(food_name.lower())
        self.serving_size = serving_size
        self.serving_units = serving_units
        for nutrient_obj in self.nutrients.values():
            setattr(self, nutrient_obj.symbol, None)

    @classmethod
    def _food_json_obj_to_nutrient_table(self, food_json_obj):
        nutrient_table = dict()
        for nutrient_json_obj in food_json_obj["foodNutrients"]:
            fdc_code = int(nutrient_json_obj["nutrient"]["number"])
            if fdc_code not in self.nutrients:
                continue
            elif "amount" not in nutrient_json_obj:
                continue
            elif float(nutrient_json_obj["amount"]) == 0:
                continue
            nutrient_table[fdc_code] = Nutrient(nutrient_json_obj["nutrient"]["name"],
                                                nutrient_json_obj["nutrient"]["unitName"].lower(),
                                                fdc_code=fdc_code,
                                                amount=float(nutrient_json_obj["amount"]),
                                                symbol=self.nutrients[fdc_code].symbol)
        return nutrient_table

    @classmethod
    def from_model_object(self, food_model_obj):
        fdc_id = food_model_obj.fdc_id
        food_name = food_model_obj.food_name
        serving_size = food_model_obj.serving_size
        serving_units = food_model_obj.serving_units
        food_obj = self(fdc_id, food_name, serving_size, serving_units)
        for fdc_id, nutrient_obj in self.nutrients:
            if not hasattr(food_model_obj, nutrient_obj.symbol):
                continue
            nutrient_in_food = nutrient_obj.copy()
            nutrient_in_food.amount = getattr(food_model_obj, nutrient_obj.symbol)
            setattr(food_obj, nutrient_obj.symbol, nutrient_in_food)
        return food_obj

    @classmethod
    def from_json_object(self, food_json_obj):
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
        for fdc_code, nutrient_obj in Food_Detailed.nutrients.items():
            if fdc_code not in nutrient_table:
                continue
            nutrient_in_food = nutrient_table[fdc_code]
            if nutrient_obj.symbol == "vitamin_D_mcg":
                # The FDC uses IU for vitamin D, but this program stores vitamin
                # D amounts in micrograms. Converting from IU to mg/mcg is
                # different for every substance that IU are used with. For
                # vitamin D, 40 IU == 1 mcg.
                nutrient_in_food.amount /= 40
                nutrient_in_food.units = 'mcg'
            setattr(food_obj, nutrient_obj.symbol, nutrient_in_food)
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

    def search_by_keywords(self, query):
        search_url = self.get_fdc_search_url()
        json_argd = dict(dataType=["Branded", "SR Legacy"], query=query)
        response = requests.post(search_url, json=json_argd)
        json_content = json.loads(response.content)
        results_list = list()
        for result_obj in json_content['foods']:
            results_list.append(Food_Stub.from_json_object(result_obj).serialize())
        return results_list

    def look_up_fdc_ids(self, fdc_ids=[]):
        results_list = list()
        for fdc_id in fdc_ids:
            lookup_url = self.get_fdc_lookup_url(fdc_id)
            response = requests.get(lookup_url)
            json_content = json.loads(response.content)
            food_obj = Food_Detailed.from_json_object(json_content)
            results_list.append(food_obj)
        return results_list

    def save_food_objs_to_db(self, food_objs):
        username = decouple.config("DB_USERNAME")
        password = decouple.config("DB_PASSWORD")
        db_conx = Db_Connection(username, password)
        return [db_conx.save_food_object(food_obj) for food_obj in food_objs]

    def retrieve_foods_list(self, food_list_page=1):
        food_list_url = self.get_food_list_url()
        json_argd = dict(dataType=["Branded", "SR Legacy"])
        if food_list_page:
            json_argd["pageNumber"] = food_list_page
        response = requests.post(food_list_url, json=json_argd)
        results_list = list()
        for response_obj in json.loads(response.content):
            food_stub_obj = Food_Stub.from_json_object(response_obj)
            results_list.append(food_stub_obj.serialize())
        return results_list
