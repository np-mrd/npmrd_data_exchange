# Run (on a local machine from "npmrd_data_exchange" repo) using this command...
# python -m conversion.curator_conversion.testing.batch_test

import os
import glob
import json
from ..npmrd_curator_converter import CuratorConverter


# First deletes all files in /test_output then runs npmrd_curator_converter.py
# on all .json files in test_input_jsons with the outputs being places in /test_output

# Define the input and output directories
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the input and output directories relative to the script directory
input_dir = os.path.join(script_dir, "test_input_jsons")
output_dir = os.path.join(script_dir, "test_output")

# input_dir = "~/Documents/SFU/lingingtonlab/submission_portal/stats/curator_backup/curator_jsons"
# output_dir = "~/Documents/SFU/lingingtonlab/submission_portal/stats/curator_backup/test_exchange_jsons"

input_dir = os.path.expanduser(input_dir)
output_dir = os.path.expanduser(output_dir)

# Find all .json files in the input directory
json_files = glob.glob(os.path.join(input_dir, "*.json"))

no_c_nmr = []
no_h_nmr = []
peak_list_only = []
non_valid = []

# Generate and run the batch commands
for input_file in json_files:
    # try:
    # Load input file as a dict
    with open(input_file, 'r') as file:
        curator_json_dict = json.load(file)
    
    # if curator_json_dict[0]['session_uuid'] != "696e25eb-0a6b-4f21-9a99-6db60c7bd80e":
    #     continue
    
    curator_converter = CuratorConverter(curator_json_dict)
    npmrd_exchange_dict, final_status_dict = curator_converter.convert_json()
    
    if final_status_dict["entries_with_no_c_nmr"]:
        no_c_nmr.append(f"{final_status_dict['session_uuid']}  {final_status_dict['doi']}")
    
    if final_status_dict["entries_with_no_h_nmr"]:
        no_h_nmr.append(f"{final_status_dict['session_uuid']}  {final_status_dict['doi']}")
        
    if final_status_dict["entries_with_peak_list_only"]:
        peak_list_only.append(f"{final_status_dict['session_uuid']}  {final_status_dict['doi']}")
    
    if not final_status_dict["valid"]:
        non_valid.append(f"{final_status_dict['session_uuid']}  {final_status_dict['doi']}")
    
    # Generate the output path
    folder_path, file_name = os.path.split(input_file)
    new_file_name = "exchange_" + file_name
    output_file_path = os.path.join(output_dir, new_file_name)

    # Write the dictionary to the new JSON file
    with open(output_file_path, 'w') as outfile:
        json.dump(npmrd_exchange_dict, outfile, indent=4)
        
    # except Exception as e:
    #     print(f"error with file {input_file} + {e}")

print({
    "no_c_nmr": no_c_nmr,
    "no_h_nmr": no_h_nmr,
    "peak_list_only": peak_list_only,
    "non_valid": non_valid
})