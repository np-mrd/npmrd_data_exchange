import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from standardization.standardizer import JSONStandardizer

standardizer = JSONStandardizer("/Users/mpin/Documents/SFU/lingingtonlab/npmrd_data_exchange/standardization/testing/test_jsons/article_json_1.json")
standardition_results = standardizer.standardize()

print("standardition_results is")
print(standardition_results)