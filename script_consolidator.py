import jsonschema
from jsonschema import exceptions
import sys
import json
from dateutil import parser
import os

from .standardization.standardizer import JSONStandardizer
from .validation.validator import JSONValidator


current_dir = os.path.dirname(os.path.abspath(__file__))
schema_file_path = os.path.join(
    current_dir, "json_schema", "npmrd-exchange_schema.json"
)
with open(schema_file_path) as f:
    json_schema = json.load(f)


class ScriptConsolidator:
    def __init__(self, json_list):
        self.json_list = json_list
        self.results = {}

    def run_scripts(self, run_schema=True, run_standardizer=True, run_validator=True):
        updated_json_list = []
        result_dict = {}
        for i, json_data in enumerate(self.json_list):
            result_dict[i] = {}
            result_dict[i]["inchikey"] = json_data.get("inchikey", "")
            result_dict[i]["source"] = json_data.get("submission", {}).get("source", "")
            result_dict[i]["type"] = json_data.get("submission", {}).get("type", "")

            if run_standardizer:
                standardizer = JSONStandardizer(json_data)
                print("json_data is")
                print(json_data)
                (
                    standardized_json_data,
                    standardizer_notes,
                ) = standardizer.standardize()
                updated_json_list.append(standardized_json_data)
                result_dict[i]["standardizer_notes"] = standardizer_notes
            else:
                updated_json_list.append(json_data)

            if run_schema:
                result_dict[i]["schema"] = {}
                result_dict[i]["schema"]["valid"] = False
                result_dict[i]["schema"]["message"] = []

                try:
                    jsonschema.validate(json_data, json_schema)
                    result_dict[i]["schema"]["valid"] = True
                except jsonschema.exceptions.ValidationError as e:
                    for error in sorted(e.path):
                        result_dict[i]["schema"]["message"] = result_dict[i]["schema"][
                            "message"
                        ].append(f"Path: {'/'.join(str(p) for p in error)}")
                except exceptions.SchemaError as e:
                    result_dict[i]["schema"]["message"] = result_dict[i]["schema"][
                        "message"
                    ].append(f"Schema error: {e}")
                except Exception as e:
                    result_dict[i]["schema"]["message"] = result_dict[i]["schema"][
                        "message"
                    ].append(f"An unexpected error occurred: {str(e)}")

            if run_validator:
                validator = JSONValidator(json_data)
                validation_results = validator.validate()
                result_dict[i]["validator"] = validation_results

        return updated_json_list, result_dict

    if __name__ == "__main__":
        if len(sys.argv) != 2:
            print("Usage: python script.py <json_file>")
        else:
            json_file_path = sys.argv[1]

            try:
                with open(json_file_path, "r") as file:
                    json_data = json.load(file)
            except FileNotFoundError:
                print(f"JSON not found: {json_data}")
            except json.JSONDecodeError:
                print(f"Provided JSON is invalid: {json_data}")

            standardizer = JSONStandardizer(json_data)
            if standardizer.standardize():
                print("All entries have been standardized.")
            else:
                print("Some entries failed standardization.")
