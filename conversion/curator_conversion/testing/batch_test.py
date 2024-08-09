import os
import glob
import json
from ..npmrd_curator_converter import CuratorConverter
# from conversion.curator_conversion.npmrd_curator_converter import CuratorConverter
# from conversion.curator_conversion.npmrd_curator_converter import CuratorConverter


# First deletes all files in /test_output then runs npmrd_curator_converter.py
# on all .json files in test_input_jsons with the outputs being places in /test_output

# Define the input and output directories
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the input and output directories relative to the script directory
input_dir = os.path.join(script_dir, "test_input_jsons")
output_dir = os.path.join(script_dir, "test_output")

# Find all .json files in the input directory
json_files = glob.glob(os.path.join(input_dir, "*.json"))

# Generate and run the batch commands
for input_file in json_files:
    # Load input file as a dict
    with open(input_file, 'r') as file:
        curator_json_dict = json.load(file)
    
    curator_converter = CuratorConverter(curator_json_dict)
    npmrd_exchange_dict = curator_converter.convert_json()
    
    # Generate the output path
    folder_path, file_name = os.path.split(input_file)
    new_file_name = "exchange_" + file_name
    output_file_path = os.path.join(output_dir, new_file_name)

    # Write the dictionary to the new JSON file
    with open(output_file_path, 'w') as outfile:
        json.dump(npmrd_exchange_dict, outfile, indent=4)
    print(f"successfully converted {output_file_path}")