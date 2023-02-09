#!/usr/bin/python3

import optparse
import decouple
import json
import requests
import sys
import subprocess

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


def main(fdc_ids=[], food_list=False, food_list_page=0):
    if fdc_ids:
        results_list = list()
        for fdc_id in fdc_ids:
            search_url = get_fdc_search_url(fdc_id)
            response = requests.get(search_url)
            this_json_bytes = response.content
            result_data = json.loads(json_bytes)
            results_list.append(result_data)
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
        arg_ints = list()
        for index, arg in enumerate(args, start=1):
            try:
                arg_ints.append(int(arg))
            except ValueError as exception:
                ordinal = number_to_ordinal(index)
                print(f"Unable to cast {ordinal} argument to int:")
                print(exception.args[0])
                exit(1)
        main(fdc_ids)
