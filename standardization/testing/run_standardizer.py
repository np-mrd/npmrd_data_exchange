import unittest
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from standardization.standardizer import JSONStandardizer

json_file_path = os.path.join("./test_jsons/article_json_1.json")
with open(json_file_path, 'r') as file:
    json_dict = json.load(file)

print("json_dict is")
print(json_dict)
print(type(json_dict))

standardizer = JSONStandardizer(json_dict)
standardition_results = standardizer.standardize()

print("standardition_results is")
print(standardition_results)