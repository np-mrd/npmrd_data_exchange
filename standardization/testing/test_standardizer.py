import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from standardization.standardizer import JSONStandardizer

class TestStandardizer(unittest.TestCase):

    def setUp(self):
        self.test_json_folder = os.path.join(os.path.dirname(__file__), 'test_jsons')
        self.article_json_1 = "article_json_1.json"
        # self.presubmission_json_1 = "presubmission_json_1.json"
        # self.private_json_1 = "private_json_1.json"
        # self.peak_list_only_json_1 = "peak_list_only_json_1.json"
        
    def test_deposition_json_1(self):
        self.run_test_for_json_file(self.article_json_1)
        
    # def test_presubmission_json_1(self):
    #     self.run_test_for_json_file(self.presubmission_json_1)
        
    # def test_private_json_1(self):
    #     self.run_test_for_json_file(self.private_json_1)
    
    # def test_peak_list_only_json_1(self):
    #     self.run_test_for_json_file(self.peak_list_only_json_1)

    def run_test_for_json_file(self, json_file):
        json_file_path = os.path.join(self.test_json_folder, json_file)
        standardizer = JSONStandardizer(json_file_path)
        standardition_results = standardizer.standardize()

        print("standardition_results is")
        print(standardition_results)

        self.assertTrue(standardition_results[0]['inchikey'] != None, f"Validation failed")

if __name__ == "__main__":
    unittest.main()
