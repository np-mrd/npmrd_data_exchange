# NP-MRD_Data_Exchange
A repo to house tools essential for data transfer between different tech stacks in the NP-MRD project. This includes the Exchange JSON format as well as validation scripts for the JSON.

## Running Validation Scripts in Python

The script can be run on an NP-MRD Exchange JSON by using the following command line command...

    python validation/validator.py NP-MRD-JSON.json

Additionally, in order to run the script within python you can also import the "JSONValidator" class and then run the "validate" command on the path to your json

    from validation.validator import JSONValidator

    json_file_path = "path/to/json.json"
    validator = JSONValidator(json_file_path)
    validation_results = validator.validate()

## Running Validation Scripts in Ruby

Because the scripts are written in python they cannot be run natively in Ruby. However, they can be run using a wrapper like such...

    require 'json'

    def run_python_script(input_data)
    output = `python validation/validator.py --input '#{input_data.to_json}'`
    JSON.parse(output)
    end

    # Example usage:
    input_data = { "key": "value" }
    result = run_python_script(input_data)
    puts result

## Testing The Validation Script

A test file to test the validator is also housed within this repo. This can be run using a unittest command like such...

    python -m unittest -v test_validator.py

Valid JSONs that are tested by this script are hosted in testing/test_jsons. test_validator.py includes to run the validator on each of these .json files.
