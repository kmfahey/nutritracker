#!/usr/bin/python3

import optparse
import sys
import subprocess
import pymongo

from utils import *


api_key = decouple.config("FDC_API_KEY")


jq_path = "/usr/bin/jq"

parser = optparse.OptionParser()
parser.add_option("-l", "--food-list", action="store_true", dest="food_list", default=False,
                  help="access the FDC /foods/list API and relay results")
parser.add_option("-p", "--food-list-page", action="store", dest="food_list_page", default=0, metavar="PAGE",
                  type="int", help="access the FDC /foods/list API and relay results")
parser.add_option("-s", "--search-foods", action="store_true", dest="search_foods", default=False,
                  help="search the FDC /foods/search API for the keywords passed as args")
parser.add_option("-d", "--save-to-db", action="store_true", dest="save_to_db", default=False,
                  help="retrieve a food object from the /food/<fdc_id> API and save it to the DB")


def main(search_kw=[], fdc_ids=[], save_to_db=False, food_list=False, food_list_page=1):
    api_contacter = Fdc_Api_Contacter(api_key)
    if save_to_db:
        food_objs = api_contacter.look_up_fdc_ids(fdc_ids)
        results_list = api_contacter.save_food_objs_to_db(food_objs)
    elif fdc_ids:
        results_list = [food_obj.serialize() for food_obj in api_contacter.look_up_fdc_ids(fdc_ids)]
    elif search_kw:
        results_list = api_contacter.search_by_keywords(' '.join(search_kw))
    elif food_list:
        results_list = api_contacter.retrieve_foods_list(food_list_page)
    else:
        return
    json_bytes = json.dumps(results_list).encode('utf-8')
    jq_proc = subprocess.Popen(jq_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    jq_stdout, jq_stderr = jq_proc.communicate(json_bytes)
    formatted_json = jq_stdout.decode('utf-8')
    print(formatted_json)


class Db_Connection:
    __slots__ = 'username', 'password', 'client', 'db'

    db_name = 'nutritracker'

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.db, self.client = get_db_handle(self.db_name, 'localhost', 27017, username, password)

    def save_food_object(self, food_obj):
        existing_food_obj = self.db.foods.find_one({'fdc_id':food_obj.fdc_id})
        if existing_food_obj is not None:
            self.db.foods.delete_one({'fdc_id':food_obj.fdc_id})
        food_obj_serialized = food_obj.serialize()
        for property_key, property_value in food_obj_serialized.items():
            if isinstance(property_value, dict):
                food_obj_serialized[property_key] = property_value["amount"]
        object_id = self.db.foods.insert_one(food_obj_serialized).inserted_id
        return str(object_id)


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
    elif options.food_list and options.search_foods:
        print("-l and -s flags both specified. These options are mutually exclusive.")
        exit(1)
    elif options.save_to_db and options.search_foods:
        print("-d and -s flags both specified. These options are mutually exclusive.")
        exit(1)
    elif options.food_list and options.save_to_db:
        print("-l and -d flags both specified. These options are mutually exclusive.")
        exit(1)
    elif options.save_to_db and not args:
        print("-d flag specified without and FDC ID arguments. Can't save to DB without FDC IDs to retrieve and save.")
        exit(1)
    elif options.search_foods and not args:
        print("-s flag specified without any keyword arguments. Can't search with an empty query.")
        exit(1)

    number_to_ordinal = lambda number: (f"{number}st" if number % 10 == 1 else
                                        f"{number}nd" if number % 10 == 2 else
                                        f"{number}rd" if number % 10 == 3 else
                                        f"{number}th")

    if options.food_list:
        main(food_list=options.food_list, food_list_page=options.food_list_page)
    elif options.search_foods:
        main(search_kw=args)
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
        main(fdc_ids=fdc_ids, save_to_db=options.save_to_db)
