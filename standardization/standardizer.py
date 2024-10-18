import sys
import json
from dateutil import parser
import traceback
import os

current_dir = os.path.dirname(__file__)
one_level_up = os.path.dirname(current_dir)
standardization_files_dir = os.path.join(one_level_up, "standardization_files")

solv_standardizer_path = os.path.join(
    standardization_files_dir, "solvent_standardizer.json"
)
vendor_standardizer_path = os.path.join(
    standardization_files_dir, "vendor_standardizer.json"
)
filetype_standardizer_path = os.path.join(
    standardization_files_dir, "filetype-name_standardizer.json"
)


class JSONStandardizer:
    def __init__(self, json_dict):
        self.json_data = json_dict
        self.notes = []
        self.rules = {
            "npmrd_id": "correct_npmrd_id",
            "submission.source": "lowercase",
            "submission.type": "lowercase",
            "submission.submission_date": "standardize_date_time",
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
            "nmr_data.peak_lists.values": "decimal_places-4",
            "nmr_data.peak_lists.temperature": "decimal_places-1",
            "nmr_data.peak_lists.frequency": "decimal_places-5",
            "nmr_data.experimental_data.nmr_metadata.vendor": "standardize_vendor",
            "nmr_data.experimental_data.nmr_metadata.filetype": "standardize_filetype",
            "nmr_data.experimental_data.nmr_metadata.temperature": "decimal_places-1",
        }

        with open(solv_standardizer_path, "r") as solv_json_file:
            self.solv_standardizer_json = json.load(solv_json_file)
        with open(vendor_standardizer_path, "r") as vendor_json_file:
            self.vendor_standardizer_json = json.load(vendor_json_file)
        with open(filetype_standardizer_path, "r") as filetype_json_file:
            self.filetype_standardizer_json = json.load(filetype_json_file)

    def _run_rule(self, current, val, field_path, rule):
        # Check if the target field exists and apply the specified rule
        if rule == "lowercase":
            # For string to be lowercase
            new_val = val.lower()
            if val != new_val:
                self.notes.append(
                    f"'{field_path}': made lowercase '{val}' -> '{new_val}'"
                )
            return new_val

        elif rule == "uppercase":
            # Force string to be uppercase
            new_val = val.upper()
            if val != new_val:
                self.notes.append(
                    f"'{field_path}': made uppercase '{val}' -> '{new_val}'"
                )
            return new_val

        elif rule == "standardize_experiment":
            pass

        elif rule == "correct_npmrd_id":
            new_val = val
            if isinstance(val, str):
                if val.startswith("NP") and val[2:].isdigit() and len(val) == 9:
                    pass  # Input is already in the correct format
                elif val.isdigit():
                    new_val = f"NP{val.zfill(7)}"
            elif isinstance(val, (int, float)):
                new_val = f"NP{int(val):07d}"

            if val != new_val:
                self.notes.append(
                    f"'{field_path}': corrected npmrd_id format '{val}' = {type(val)} -> '{new_val}' = {type(new_val)}"
                )
            return new_val

        elif rule == "standardize_solvent":
            # Convert known solvents to standardized format
            if val.upper() in self.solv_standardizer_json.keys():
                new_val = self.solv_standardizer_json[val.upper()]
                if val != new_val:
                    self.notes.append(
                        f"'{field_path}': solvent standardized '{val}' -> '{new_val}'"
                    )
                return new_val
            else:
                return val

        elif rule == "standardize_vendor":
            # Convert known vendor names to standardized format
            if val.upper() in self.vendor_standardizer_json.keys():
                new_val = self.vendor_standardizer_json[val.upper()]
                if val != new_val:
                    self.notes.append(
                        f"'{field_path}': made int '{val}' = {type(val)} -> '{new_val}' = {type(new_val)}"
                    )
                return new_val
            else:
                return val

        elif rule == "standardize_filetype":
            # Convert known vendor names to standardized format
            if val.upper() in self.filetype_standardizer_json.keys():
                new_val = self.filetype_standardizer_json[val.upper()]
                if val != new_val:
                    self.notes.append(
                        f"'{field_path}': filetype standardized '{val}' -> '{new_val}'"
                    )
                return new_val
            else:
                return val

        elif rule == "make_int":
            # Convert to int
            new_val = int(val)
            if val != new_val:
                self.notes.append(
                    f"'{field_path}': made int '{val}' = {type(val)} -> '{new_val}' = {type(new_val)}"
                )
            return new_val

        elif rule == "make_float":
            # Convert to float
            new_val = float(val)
            if val != new_val:
                self.notes.append(
                    f"'{field_path}': made float '{val}' = {type(val)} -> '{new_val}' = {type(new_val)}"
                )
            return new_val

        elif rule == "make_bool":
            # Convert to bool of True, False, or None
            new_val = val
            if isinstance(val, bool):
                pass
            elif isinstance(val, int):
                new_val = bool(val)
            elif isinstance(val, str):
                val_str = val.lower().strip()
                if val_str in ["true", "1"]:
                    new_val = True
                elif val in ["false", "0"]:
                    new_val = False
                else:
                    new_val = None

            if val != new_val:
                self.notes.append(
                    f"'{field_path}': made bool '{val}' = {type(val)} -> '{new_val}' = {type(new_val)}"
                )
            return new_val

        elif rule.startswith("decimal_places"):
            # Specify how many decimal places to use after the "-""
            # i.e. "decimal_places-2" will limit to 2 decimals places
            path_parts = rule.split("-")

            if type(val) == list:
                new_val = []
                for val_entry in val:
                    new_val.append(float(round(val_entry, int(path_parts[-1]))))
            else:
                new_val = float(round(val, int(path_parts[-1])))

            if val != new_val:
                self.notes.append(
                    f"'{field_path}': adjusted to go to {path_parts[-1]} decimal places '{val}' = {type(val)} -> '{new_val}' = {type(new_val)}"
                )
            return new_val

        elif rule == "standardize_date_time":
            # Convert date to standardized format
            new_val = parser.parse(val).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
            if val != new_val:
                self.notes.append(
                    f"'{field_path}': standardized date/time format '{val}' = {type(val)} -> '{new_val}' = {type(new_val)}"
                )
            return new_val

        elif rule == "standardize_date":
            # Convert date to standardized format and remove time (retain only date)
            midnight_date = val.replace(hour=0, minute=0, second=0, microsecond=0)
            new_val = parser.parse(val).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
            if val != new_val:
                self.notes.append(
                    f"'{field_path}': standardized date format '{val}' = {type(val)} -> '{new_val}' = {type(new_val)}"
                )
            return new_val

        return

    def _traverse_json(self, json_data, field_path, rule):
        # Split the field path into parts based on dot notation
        path_parts = field_path.split(".")

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

        # run rule if field exists and is not None
        if target_field in current and current[target_field] is not None:
            # If target_field is a list then apply the rule to each entry
            if type(current[target_field]) == list:
                new_list = []
                for target_field_entry in current[target_field]:
                    new_val = self._run_rule(
                        current, target_field_entry, field_path, rule
                    )
                    if new_val:
                        new_list.append(new_val)
                    else:
                        new_list.append(target_field_entry)
                current[target_field] = new_list

            # Else run on the target_field value directly
            else:
                new_val = self._run_rule(
                    current, current[target_field], field_path, rule
                )
                if new_val:
                    current[target_field] = new_val

        return

    def _run_standardizer(self, json_data_list):
        """Standardize each dictionary in a list of dictionaries."""
        for json_data in json_data_list:
            for key, value in json_data.items():
                # Trim whitespace from all str entries
                if isinstance(value, str):
                    strip_value = value.strip()
                    if strip_value == "":
                        json_data[key] = None
                    else:
                        json_data[key] = strip_value

            # Apply "rules" to appropriate fields in json
            for field_path, rule in self.rules.items():
                self._traverse_json(json_data, field_path, rule)
        
        return json_data_list, self.notes

    def standardize(self):
        """
        Used to run the standardization of an NP-MRD Exchange JSON.

        Returns:
            list:

        Example Output:

        """
        try:
            standardized_json = self._run_standardizer(self.json_data)
            return standardized_json

        except Exception:
            print(f"An error occurred: {traceback.format_exc()}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <json_file>")
    else:
        json_file_path = sys.argv[1]

        try:
            with open(json_file_path, "r") as file:
                json_dict = json.load(file)
        except FileNotFoundError:
            print(f"JSON not found: {json_dict}")
        except json.JSONDecodeError:
            print(f"Provided JSON is invalid: {json_dict}")

        standardizer = JSONStandardizer(json_dict)
        if standardizer.standardize():
            print("All entries have been standardized.")
        else:
            print("Some entries failed standardization.")
