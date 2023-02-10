#!/usr/bin/python3

import optparse
import decouple
import json
import requests
import sys
import subprocess
import re


#api_url = "https://api.nal.usda.gov/fdc/v1/foods/list"

api_url = "https://api.nal.usda.gov/fdc/v1"

api_key = decouple.config("FDC_API_KEY")

get_fdc_search_url = lambda fdc_id, page_number=1: f"{api_url}/food/{fdc_id}?api_key={api_key}"
get_food_list_url = lambda: f"{api_url}/foods/list?api_key={api_key}"

jq_path = "/usr/bin/jq"

parser = optparse.OptionParser()
parser.add_option("-l", "--food-list", action="store_true", dest="food_list", default=False, help="access the FDC /foods/list API and relay results")
parser.add_option("-p", "--food-list-page", action="store", dest="food_list_page", default=0, metavar="PAGE", type="int", help="access the FDC /foods/list API and relay results")

number_to_ordinal = lambda number: (f"{number}st" if number % 10 == 1 else
                                    f"{number}nd" if number % 10 == 2 else
                                    f"{number}rd" if number % 10 == 3 else
                                    f"{number}th")



class Nutrient:
    __slots__ = ('name', 'units', 'fdc_code', 'amount', 'symbol')

    def __init__(self, name, units, fdc_code=0, amount=0, symbol=''):
        self.name = name
        self.units = units
        self.fdc_code = fdc_code
        self.amount = amount
        self.symbol = symbol


class Food:
    __slots__ = ('fdc_id', 'food_name', 'serving_size', 'serving_units', 'biotin_mcg', 'calcium_mg', 'cholesterol_mg',
                 'copper_mg', 'dietary_fiber_g', 'energy_kcal', 'folate_mcg', 'iodine_mcg', 'iron_mg', 'magnesium_mg',
                 'niacin_B6_mg', 'pantothenic_acid_B5_mg', 'phosphorous_mg', 'potassium_mg', 'protein_g',
                 'riboflavin_B2_mg', 'saturated_fat_g', 'sodium_mg', 'sugars_g', 'thiamin_B1_mg',
                 'total_carbohydrates_g', 'total_fat_g', 'trans_fat_g', 'vitamin_D_mcg', 'vitamin_E_mg', 'zinc_mg')

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
        406: Nutrient("niacin (vitamin B6) (mg)", "mg", fdc_code=406, symbol='niacin_B6_mg'),
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

    is_unc_alnum_punct = lambda self, strval: re.match("^[A-Za-zÀ-ÿ0-9._'ʼ’]+$", strval)

    capitalize = lambda self, strval: re.sub("[A-Za-zÀ-ÿ]", lambda m: m.group(0).upper(), strval, count=1)

    def __init__(self, fdc_id, food_name, serving_size, serving_units):
        self.fdc_id = fdc_id
        self.food_name = food_name
        self.serving_size = serving_size
        self.serving_units = serving_units
        for nutrient_obj in self.nutrients.values():
            setattr(self, nutrient_obj.symbol, 0)

    @classmethod
    def _title_case(strval):

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
            if self.is_unc_alnum_punct(token):
                first_alpha_token_index = index
                break
        for index, token in zip(range(len(tokens) - 1, -1, -1), reversed(tokens)):
            if self.is_unc_alnum_punct(token):
                last_alpha_token_index = index
                break

        for index in range(len(tokens)):
            token = tokens[index]
            if re.match(r"^([A-Za-zÀ-ÿ]\.){2,}$", token):
                token = token.upper()
            elif index == first_alpha_token_index or index == last_alpha_token_index:
                token = self.capitalize(token)
            elif token.lower() in title_case_lc_words:
                token = token.lower()
            elif re.match("^([à-ÿa-z'’ʼ]+)$", token):
                token = self.capitalize(token)
            output.append(token)

        return ''.join(output)

    @classmethod
    def _food_json_obj_to_nutrient_table(self, food_json_obj):
        nutrient_table = dict()
        for nutrient_json_obj in food_json_obj["foodNutrients"]:
            fdc_code = int(nutrient_json_obj["nutrient"]["number"])
            if fdc_code not in self.nutrients:
                continue
            elif "amount" not in nutrient_json_obj:
                continue
            nutrient_table[fdc_code] = Nutrient(nutrient_json_obj["nutrient"]["name"],
                                                nutrient_json_obj["nutrient"]["unitName"].lower(),
                                                amount=float(nutrient_json_obj["amount"]))
        return nutrient_table

    @classmethod
    def from_json_object(self, food_json_obj):
        fdc_id = food_json_obj["fdcId"]
        food_name = self._title_case(food_json_obj["description"].lower().strip())
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
        for fdc_code, nutrient_obj in Food.nutrients.items():
            if fdc_code not in nutrient_table:
                continue
            nutrient_in_food = nutrient_table[fdc_code]
            if nutrient_obj.symbol == "vitamin_D_mcg":
                # The FDC uses IU for vitamin D, but this program stores vitamin
                # D amounts in micrograms. Converting from IU to mg/mcg is
                # different for every substance that IU are used with. For
                # vitamin D, 40 IU == 1 mcg.
                nutrient_amount = nutrient_in_food.amount / 40
            else:
                assert nutrient_in_food.units == self.nutrients[fdc_code].units
                nutrient_amount = nutrient_in_food.amount
            setattr(food_obj, nutrient_obj.symbol, nutrient_amount)
        return food_obj

    def serialize(self):
        return {attr_name: getattr(self, attr_name) for attr_name in self.__slots__ if getattr(self, attr_name)}


def main(fdc_ids=[], food_list=False, food_list_page=0):
    if fdc_ids:
        results_list = list()
        for fdc_id in fdc_ids:
            search_url = get_fdc_search_url(fdc_id)
            response = requests.get(search_url)
            json_content = json.loads(response.content)
            food_obj = Food.from_json_object(json_content)
            results_list.append(food_obj.serialize())
        json_bytes = json.dumps(results_list).encode('utf-8')
    elif food_list:
        food_list_url = get_food_list_url()
        json_argd = dict(dataType=["Branded", "SR Legacy"])
        if food_list_page:
            json_argd["pageNumber"] = food_list_page
        response = requests.post(food_list_url, json=json_argd)
        json_bytes = response.content
    else:
        return
    jq_proc = subprocess.Popen(jq_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    jq_stdout, jq_stderr = jq_proc.communicate(json_bytes)
    formatted_json = jq_stdout.decode('utf-8')
    print(formatted_json)


if __name__ == "__main__":
    (options, args) = parser.parse_args()

    if options.food_list and args:
        print("-l flag was specified but non-option arguments included on commandline. Cannot process non-option arguments in list mode.")
        exit(1)
    elif options.food_list_page != 0 and options.food_list is False:
        print("-p flag was specified but -l flag was not. Cannot use a page number value when not in list mode.")
        exit(1)
    elif options.food_list_page < 0:
        print(f"-p flag was specified with an argument that's less than zero. {options.food_list_page} cannot be a valid page number.")
        exit(1)

    if options.food_list:
        main(food_list=options.food_list, food_list_page=options.food_list_page)
    elif args:
        fdc_ids = list()
        for index, arg in enumerate(args, start=1):
            try:
                fdc_ids.append(int(arg))
            except ValueError as exception:
                ordinal = number_to_ordinal(index)
                print(f"Unable to cast {ordinal} argument to int:")
                print(exception.args[0])
                exit(1)
        main(fdc_ids)
