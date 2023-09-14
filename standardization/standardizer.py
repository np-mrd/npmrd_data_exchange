import sys
import json
from dateutil import parser
import os

# with open('../standardization_files/experiment_standarizer.json', 'r') as json_file:
#     exp_standardizer_json = json.load(json_file)

current_dir = os.path.dirname(__file__)
one_level_up = os.path.dirname(current_dir)
standardization_files_dir = os.path.join(one_level_up, 'standardization_files')

solv_standardizer_path = os.path.join(standardization_files_dir, 'solvent_standardizer.json')
vendor_standardizer_path = os.path.join(standardization_files_dir, 'vendor_standardizer.json')
filetype_standardizer_path = os.path.join(standardization_files_dir, 'filetype-name_standardizer.json')
    
class JSONStandardizer:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.results = []
        self.rules = {
            "npmrd_id": "upper",
            "submission.source": "lowercase",
            "submission.type": "lowercase",
            "submission.submission_date": "standardize_date",
            "submission.embargo_status": "lowercase",
            "submission.embargo_date": "standardize_date",
            "citation.pmid": "make_int",
            "origin.private_collection.compound_source_type": "lowercase",
            "depositor_info.email": "lowercase",
            "depositor_info.account_id": "make_int",
            "depositor_info.show_email_in_attribution": "make_bool",
            "depositor_info.show_name_in_attribution": "make_bool",
            "depositor_info.show_organization_in_attribution": "make_bool",
            "nmr_data.peak_lists.solvent": "standardize_solvent",
            "nmr_data.peak_lists.c_values": "decimal_places-3",
            "nmr_data.peak_lists.h_values": "decimal_places-3",
            "nmr_data.peak_lists.c_frequency": "decimal_places-3",
            "nmr_data.peak_lists.h_frequency": "decimal_places-3",
            "nmr_data.peak_lists.h_temperature": "decimal_places-1",
            "nmr_data.peak_lists.c_temperature": "decimal_places-1",
            "nmr_data.experimental_data.nmr_metadata.vendor": "standardize_vendor",
            "nmr_data.experimental_data.nmr_metadata.filetype": "standardize_filetype",
            "nmr_data.experimental_data.nmr_metadata.frequency": "decimal_places-8",
            "nmr_data.experimental_data.nmr_metadata.temperature": "decimal_places-1",
        }
                
        with open(solv_standardizer_path, 'r') as solv_json_file:
            self.solv_standardizer_json = json.load(solv_json_file)
        with open(vendor_standardizer_path, 'r') as vendor_json_file:
            self.vendor_standardizer_json = json.load(vendor_json_file)
        with open(filetype_standardizer_path, 'r') as filetype_json_file:
            self.filetype_standardizer_json = json.load(filetype_json_file)
            
    def _run_rule(self, current, val, rule):
        # Check if the target field exists and apply the specified rule
        if rule == 'lowercase':
            # For string to be lowercase
            return val.lower()
            
        elif rule == 'upper':
            # Force string to be uppercase
            return val.upper()
            
        elif rule == "standardize_experiment":
            pass
        
        elif rule == "standardize_solvent":
            # Convert known solvents to standardized format
            if val.upper() in self.solv_standardizer_json.keys():
                return self.solv_standardizer_json[val.upper()]
            else:
                return val
        
        elif rule == "standardize_vendor":
            # Convert known vendor names to standardized format
            if val.upper() in self.vendor_standardizer_json.keys():
                return self.vendor_standardizer_json[val.upper()]
            else:
                return val
        
        elif rule == "standardize_filetype":
            # Convert known vendor names to standardized format
            if val.upper() in self.filetype_standardizer_json.keys():
                return self.filetype_standardizer_json[val.upper()]
            else:
                return val
        
        elif rule == "make_int":
            # Convert to int
            return int(val)

        elif rule == "make_float":
            # Convert to float
            return float(val)
            
        elif rule == "make_bool":
            # Convert to bool of True, False, or None
            if isinstance(val, bool):
                pass
            elif isinstance(val, int):
                return bool(val)
            elif isinstance(val, str):
                val = val.lower().strip()
                if val in ["true", "1"]:
                    return True
                elif val in ["false", "0"]:
                    return False
                else:
                    return None
            else:
                return None
    
        elif rule.startswith("decimal_places"):
            # Specify how many decimal places to use after the "-""
            # i.e. "decimal_places-2" will limit to 2 decimals places
            path_parts = rule.split("-")
            return float(round(val, int(path_parts[-1])))
                
        elif rule == "standardize_date":
            # Convert date to standardized format
            return parser.parse(val).strftime('%Y-%m-%dT%H:%M:%S.%f+00:00')
    
        return


    def _traverse_json(self, json_data, field_path, rule):
        # Split the field path into parts based on dot notation
        path_parts = field_path.split('.')

        # Navigate through the nested dictionary to the target field
        target_field = path_parts[-1]
        
        current = json_data
        for _ in range(len(path_parts) - 1):
            part = path_parts.pop(0)
            current = current.get(part, {})
            # If entry is a list then create a loop and recursively check each entry
            if type(current) == list:
                # If there is a still a dict to traverse then do so
                current_first = current[0] if current else None
                if type(current_first) == dict:
                    for current_entry in current:
                        loop_path_parts = ".".join(path_parts)
                        self._traverse_json(current_entry, loop_path_parts, rule)
                    return json_data
        
        # run rule
        if target_field in current and current[target_field] is not None:
            # If target_field is a list then apply the rule to each entry
            if type(current[target_field]) == list:
                new_list = []
                for target_field_entry in current[target_field]:
                    new_val = self._run_rule(current, target_field_entry, rule)
                    if new_val:
                        new_list.append(new_val)
                    else:
                        new_list.append(target_field_entry)
                current[target_field] = new_list
                
            # Else run on the target_field value directly
            else:
                new_val = self._run_rule(current, current[target_field], rule)
                if new_val:
                    current[target_field] = new_val

        return


    def _run_standardizer(self, json_data):        
        # Trim whitespace from all str entries
        for key, value in json_data.items():
            if isinstance(value, str):
                json_data[key] = value.strip()
        
        # Apply "rules" to appropriate fields in json
        for field_path, rule in self.rules.items():
            self._traverse_json(json_data, field_path, rule)

        return json_data


    def standardize(self):
        """
        Used to run the standardization of an NP-MRD Exchange JSON. 

        Returns:
            list: 

        Example Output:

        """
        try:
            with open(self.json_file_path, 'r') as file:
                json_list = json.load(file)

            standardized_json_list = []
            for i, json_data in enumerate(json_list):
                standardized_json_list.append(
                    self._run_standardizer(json_data)
                )

            # # Save the standardized data in a new file with a standardized name
            # with open(output_file, 'w') as file:
            #     json.dump(standardized_json_list, file, indent=4)

            return standardized_json_list

        except FileNotFoundError:
            print(f"File not found: {self.json_file_path}")
        except json.JSONDecodeError:
            print(f"Invalid JSON in file: {self.json_file_path}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <json_file>")
    else:
        json_file_path = sys.argv[1]
        standardizer = JSONStandardizer(json_file_path)
        if standardizer.standardize():
            print("All entries have been standardized.")
        else:
            print("Some entries failed standardization.")
