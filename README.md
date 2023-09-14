# NP-MRD_Data_Exchange
A repo to house tools essential for data transfer between different tech stacks in the NP-MRD project. This includes the Exchange JSON format as well as validation scripts for the JSON.

## Using This Repo as a Submodule

In order to maintain consistence between different tools in the NP-MRD family this repo houses important standardization files (standardization_files) used to define the json exchange schema (npmrd-exchange_schema.json), experiment name standardization (experiment_standardizer.json), and solvent naming standardization (solvent_standardizer.json). If you wish to use any of these files or validation scripts in the context of a larger repo then you can add this repo as a subdirectory to your project via the following command...

```
git submodule add https://github.com/np-mrd/npmrd_data_exchange.git <path_to_submodule_directory>
```

Then, whenever there is an update to any of the files in this repo, you can update them in your repo by running an update command

```
git submodule update
```

# JSON Parameter Outline

For information on what is expected from an NP-MRD Exchange JSON please view the documentation pertaining to it: [npmrd_cross_domain_integration_docs](https://github.com/np-mrd/npmrd_cross_domain_integration_docs).

# JSON Schema Validation

Included in this repo is a json schema file `standardization_files/npmrd-exchange_schema.json`. Validation against this JSON will achieve the following effects...

- Ensure required fields FOR ALL EXCHANGE PURPOSES are included (i.e. smiles, submission.source, etc.). Note that field requirements for specific purposes (i.e. deposition) are checked with the custom validation script.
- Ensure each field is in the correct data type
- Ensure that strings are an accepted length
- Ensure that certain numeric fields have minimum or maximum values



## Running JSON Schema Validation

JSON Validaiton can be performed by running the JSON schema (`standardization_files/npmrd-exchange_schema.json`) against any NP-MRD JSON that is to be deposited. Note that the exchange JSON will always be a list of multiple entries, even if there is only a single entry.

### Running JSON Schema Validation in Python

JSON Schema validation can be performed using a variety of different third party python libraries.

Using the "jsonschema" library you can do the following...

```
import jsonschema
from jsonschema import validate
import json

# Load the JSON schema from a file
with open("standardization_files/npmrd-exchange_schema.json", "r") as schema_file:
    schema = json.load(schema_file)

# Load the JSON data to validate from a file
with open("NP-MRD_JSON.json", "r") as data_file:
    data = json.load(data_file)

try:
    validate(instance=JSON_FILE, schema=SCHEMA_FILE)
    print("Validation successful.")
except jsonschema.exceptions.ValidationError as e:
    print(f"Validation failed: {e}")
```

# Custom Standardization Script

In addition to the json Schema there are also custom standardization python scripts that have been prepared for the purpose of performing conversion from common alternatives that may be present in NP-MRD jsons as a result of producing them in different environments. This includes...

- Converting numeric strings to numeric variables
- Standardizing boolean fields to True/False
- Forcing upper/lowercase of certain strings
- Standardizing date formats
- Setting a limit on the number of decimals
- Standardizing vendor naming
- Standardizing filetype naming

# Custom Validation Script

A validation script has been setup `validation/validator.py`. This validation script exists to ensure that, given a specified purpose of the json (i.e. submission.source) that specific fields are present within the JSON. Essentially this script exists to perform checks of an NP-MRD Exchange json in ways that are more complicated than is possible with simple schema validation.

- The inclusion of purpose specific fields (i.e. deposition related jsons MUST have a submission.type, submission.uuid, etc.)
- Ensure that if two fields rely on each other that they are both filled out correctly (i.e. if depositor_info.show_name_in_attribution is True then ensure a depositor_info.attribution_name is non-null)

# Running Custom Scripts

## Running Scripts in Python

The script can be run on an NP-MRD Exchange JSON by using the following command line command...



Additionally, in order to run the script within python you can also import the "JSONStandardizer" class and then run the "standardize" command on the path to your json

```
from validation.validator import JSONValidator

json_file_path = "path/to/json.json"
```

## Running Validation Scripts in Python

The scripts can be run on an NP-MRD Exchange JSON by using the following command line commands...

```
python validation/validator.py NP-MRD-JSON.json

python standardization/standardizer.py NP-MRD-JSON.json
```

Additionally, in order to run the script within python you can also import the "JSONValidator" class and then run the "validate" command on the path to your json

```
json_file_path = "path/to/json.json"

from validation.validator import JSONValidator
validator = JSONValidator(json_file_path)
validation_results = validator.validate()

from JSONStandardizer.standardizer import JSONStandardizer
standardizer = JSONStandardizer(json_file_path)
standardition_results = standardizer.standardize()
```

## Running Validation Scripts in Ruby

Because the scripts are written in python they cannot be run natively in Ruby. However, they can be run using a wrapper like such...

```
require 'json'

def run_python_script(input_data)
output = `python validation/validator.py --input '#{input_data.to_json}'`
JSON.parse(output)
end

# Example usage:
input_data = { "key": "value" }
result = run_python_script(input_data)
puts result
```

## Testing Custom Script

Test files for the custom scripts are also housed within this repo. They can be run using a unittest command like such...

```
python -m unittest -v validation/testing/test_validator.py

python -m unittest -v standardization/testing/test_standardizer.py 
```
