import os
import glob

# First deletes all files in /test_output then runs npmrd_curator_converter.py
# on all .json files in test_input_jsons with the outputs being places in /test_output

# Define the input and output directories
input_dir = "test_input_jsons"
output_dir = "test_output"
schema_file = "../../json_schema/npmrd-exchange_schema.json"

# Find all .json files in the input directory
json_files = glob.glob(os.path.join(input_dir, "*.json"))

# Generate and run the batch commands
for input_file in json_files:
    # Split the input_file into folder path and file name
    folder_path, file_name = os.path.split(input_file)
    
    # Append "exchange_" to the file name
    new_file_name = "exchange_" + file_name
    
    # Combine the output directory with the new file name
    output_file = os.path.join(output_dir, new_file_name)
    
    # Create the command
    command = f"python ../npmrd_curator_converter.py {input_file} {schema_file} {output_file}"
    
    # Print the command (or you could use os.system(command) to run it directly)
    print(command)
    os.system(command)