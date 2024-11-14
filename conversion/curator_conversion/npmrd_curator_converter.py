import json
import os
import pandas as pd
import jsonschema
import traceback
import uuid
import copy

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to the schema file one directory level up from the script's directory
schema_file_path = os.path.join(script_dir, '..', '..', 'json_schema', 'npmrd-exchange_schema.json')

class CuratorConverter:
    """
    Converts json output by the NP-MRD Curator to the standardized json format within the
    "npmrd-exchange_schema.json" file. Returns a full exchange format JSON. Assignment data
    in the curator JSON is contained in the nmr_data/assignment_data list. All available
    compound data is included (compound_name, smiles, species, genus, doi, etc.) However
    please note the following...
        - nmr_data/peak_lists is always forced to be an empty list
        - nmr_data/experimental_data/nmr_metadata is always forced to be an empty list
        - An assignment_uuid IS NOT ASSIGNED. This is must be done by the submission platform
        backend so that it can be properly saved / kept track of.
    
    Example usage to convert a "curator_json_dict" (converted to a Dict)
        curator_converter = CuratorConverter(curator_json_dict)
        npmrd_exchange_dict = curator_converter.convert_json()
    
    Returns:
        npmrd_exchange_dict: Dict of generated npmrd-exchange_schema
    """
    def __init__(self, curator_json_dict):
        self.curator_json_dict = curator_json_dict
        self.schema = self.load_schema_json(schema_file_path)

    @staticmethod
    def load_schema_json(file_path):
        """Load JSON data from a file."""
        try:
            with open(file_path, 'r') as file:
                schema = json.load(file)
            return schema
        except FileNotFoundError:
            print(f"The schema file was not found at `{file_path}`")
        except json.JSONDecodeError as e:
            print(f"Error decoding the JSON file: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def generate_empty_value(self, schema):
        schema_type = schema.get("type")
        default_value = schema.get("default")
        
        if default_value is not None:
            return default_value
        elif schema_type == "object":
            return {key: self.generate_empty_value(value) for key, value in schema.get("properties", {}).items()}
        elif schema_type == "array":
            items_schema = schema.get("items")
            if isinstance(items_schema, list):
                return [self.generate_empty_value(item) for item in items_schema]
            elif isinstance(items_schema, dict):
                return [self.generate_empty_value(items_schema)] if items_schema else []
            else:
                return []
        elif schema_type == "string":
            return ""
        elif schema_type == "integer":
            return 0
        elif schema_type == "number":
            return 0.0
        elif schema_type == "boolean":
            return False
        elif schema_type == "null":
            return None
        else:
            return None

    def remove_default_empty_list(self, schema, target_paths, current_path=""):
        """
        Recursively traverses the schema and removes the 'default' value (empty list) at the specified target paths.
        
        :param schema: The JSON schema being traversed.
        :param target_paths: A list of paths where the 'default' value (empty list) should be removed, in dot notation.
        :param current_path: The current path in the traversal (used internally by the function).
        :return: The updated schema with the empty list 'default' removed at the specified paths.
        """
        if not isinstance(schema, dict):
            return schema

        # Check if the current path matches any target path and remove the default if so
        if any(current_path == target for target in target_paths) and "default" in schema and schema["default"] == []:
            del schema["default"]

        # If the schema has properties, recurse into each property
        if schema.get("type") == "object" and "properties" in schema:
            for key, value in schema["properties"].items():
                new_path = f"{current_path}.{key}" if current_path else key
                schema["properties"][key] = self.remove_default_empty_list(value, target_paths, new_path)

        # If the schema has items (for arrays), recurse into items
        elif schema.get("type") == "array" and "items" in schema:
            items_schema = schema["items"]
            new_path = f"{current_path}" if current_path else "items"
            if isinstance(items_schema, dict):
                # If items is a dict, handle it as an object
                schema["items"] = self.remove_default_empty_list(items_schema, target_paths, new_path)
            elif isinstance(items_schema, list):
                # If items is a list, handle each item individually
                for idx, item_schema in enumerate(items_schema):
                    new_item_path = f"{new_path}[{idx}]" if current_path else f"items[{idx}]"
                    schema["items"][idx] = self.remove_default_empty_list(item_schema, target_paths, new_item_path)

        return schema

    def generate_json_from_schema(self):
        schema_copy = copy.deepcopy(self.schema)
        return self.generate_empty_value(schema_copy)
    
    def generate_empty_json_from_schema(self):
        schema_copy = copy.deepcopy(self.schema)
        return self.generate_empty_value(schema_copy)

    def get_empty_assignment_data_from_schema(self):
        empty_defaults_to_remove = [
            "nmr_data.assignment_data"
        ]
        non_empty_schema = copy.deepcopy(self.schema)
        non_empty_schema = self.remove_default_empty_list(non_empty_schema, empty_defaults_to_remove) 
        empty_entry = self.generate_empty_value(schema=non_empty_schema)['nmr_data']['assignment_data'][0]
        return empty_entry
    
    def get_empty_c_spectrum_from_schema(self):
        empty_defaults_to_remove = [
            "nmr_data.assignment_data",
            "nmr_data.assignment_data[0].c_nmr.spectrum"
        ]
        non_empty_schema = copy.deepcopy(self.schema)        
        non_empty_schema = self.remove_default_empty_list(non_empty_schema, empty_defaults_to_remove)
        empty_entry = self.generate_empty_value(schema=non_empty_schema)['nmr_data']['assignment_data'][0]['c_nmr']['spectrum'][0]
        return empty_entry
    
    def get_empty_h_spectrum_from_schema(self):
        empty_defaults_to_remove = [
            "nmr_data.assignment_data",
            "nmr_data.assignment_data[0].h_nmr.spectrum"
        ]
        non_empty_schema = copy.deepcopy(self.schema)
        non_empty_schema = self.remove_default_empty_list(non_empty_schema, empty_defaults_to_remove)
        return self.generate_empty_value(schema=non_empty_schema)['nmr_data']['assignment_data'][0]['h_nmr']['spectrum'][0]

    def strip_white_space(self, string):
        return string.strip() if string else ''


    def convert_json(self):
        """Update the schema with data from the input JSON."""
        final_json_list = []
        final_status_dict = {
            "converted": True,
            "valid": True,
            "validation_error": "",
            "session_uuid": "",
            "doi": "",
            "entries_with_no_c_nmr": False,
            "entries_with_no_h_nmr": False,
            "entries_with_peak_list_only": False
        }
        
        try:
            final_status_dict["session_uuid"] = self.curator_json_dict[0]['session_uuid']
            final_status_dict["doi"] = self.curator_json_dict[0]['origin_doi']
        except:
            pass

        # Iterate through full input json
        for curator_entry in self.curator_json_dict:
            new_json = self.generate_empty_json_from_schema()
            new_json['compound_name'] = self.strip_white_space(curator_entry['name'])
            new_json['np_mrd_id'] = None
            new_json['smiles'] = self.strip_white_space(curator_entry['smiles'])
            new_json['citation']['doi'] = self.strip_white_space(curator_entry['origin_doi'])
            new_json['origin']['genus'] = self.strip_white_space(curator_entry['origin_genus'])
            new_json['origin']['species'] = self.strip_white_space(curator_entry['origin_species'])
            new_json['submission']['source'] = "npmrd_curator"
            new_json['nmr_data']['experimental_data']['nmr_metadata'] = []
            new_json['nmr_data']['peak_lists'] = []
            new_json['submission']['source'] = "npmrd_curator"
            
            # Entries to fill out the "assignment_data" list of the exchange json with.
            # Typically one for C and one for H
            new_assignment_entry = self.get_empty_assignment_data_from_schema()
            
            new_assignment_entry['curator_email_address'] = self.strip_white_space(curator_entry['curator_email_address'])
            new_assignment_entry['rdkit_version'] = curator_entry['rdkit_version']
            
            new_assignment_entry['canonicalized_mol_block'] = curator_entry['canonicalized_mol_block']
            
            new_assignment_uuid_c = str(uuid.uuid4())
            new_assignment_uuid_h = str(uuid.uuid4())
            
            if len(curator_entry['c_nmr']['spectrum']) > 0:
                # Check if rdkit_index is present in nmr. If it isn't then assume this is a peak list.
                if (
                    not "rdkit_index" in curator_entry['c_nmr']['spectrum'][0]
                    or not curator_entry['c_nmr']['spectrum'][0]["rdkit_index"]
                ):
                    final_status_dict['entries_with_peak_list_only'] = True
                    continue
                
                new_assignment_entry['c_nmr']['assignment_uuid'] = new_assignment_uuid_c
                new_assignment_entry['c_nmr']['solvent'] = curator_entry['c_nmr']['solvent']
                if curator_entry['c_nmr']['temperature']: # Temperature can be empty string (not accepted) so make sure there's a value
                    new_assignment_entry['c_nmr']['temperature'] = int(curator_entry['c_nmr']['temperature'])
                new_assignment_entry['c_nmr']['temperature_units'] = "K"
                new_assignment_entry['c_nmr']['reference'] = curator_entry['c_nmr']['reference']
                new_assignment_entry['c_nmr']['frequency'] = curator_entry['c_nmr']['frequency']
                new_assignment_entry['c_nmr']['frequency_units'] = "MHz"
                new_assignment_entry['c_nmr']['assignment_data_embargo_release_ready'] = None
                
                new_spectrum_list = []
                
                for curator_c_spectrum in curator_entry['c_nmr']['spectrum']:
                    new_c_spectrum_entry = self.get_empty_c_spectrum_from_schema()
                    new_c_spectrum_entry['shift'] = curator_c_spectrum['shift']
                    new_c_spectrum_entry['mol_block_index'] = [curator_c_spectrum['rdkit_index']]
                    new_spectrum_list.append(new_c_spectrum_entry)

                new_assignment_entry['c_nmr']['spectrum'] = new_spectrum_list
            else:
                final_status_dict['entries_with_no_c_nmr'] = True


            if len(curator_entry['h_nmr']['spectrum']) > 0:
                # Check if rdkit_index is present in nmr. If it isn't then assume this is a peak list.
                if (
                    not "rdkit_index" in curator_entry['h_nmr']['spectrum'][0]
                    or not curator_entry['h_nmr']['spectrum'][0]["rdkit_index"]
                ):
                    final_status_dict['entries_with_peak_list_only'] = True
                    continue
                
                new_assignment_entry['h_nmr']['assignment_uuid'] = new_assignment_uuid_h
                new_assignment_entry['h_nmr']['solvent'] = curator_entry['h_nmr']['solvent']
                if curator_entry['h_nmr']['temperature']: # Temperature can be empty string (not accepted) so make sure there's a value
                    new_assignment_entry['h_nmr']['temperature'] = int(curator_entry['h_nmr']['temperature'])
                new_assignment_entry['h_nmr']['temperature_units'] = "K"
                new_assignment_entry['h_nmr']['reference'] = curator_entry['h_nmr']['reference']
                new_assignment_entry['h_nmr']['frequency'] = curator_entry['h_nmr']['frequency']
                new_assignment_entry['h_nmr']['frequency_units'] = "MHz"
                new_assignment_entry['h_nmr']['assignment_data_embargo_release_ready'] = None
                
                new_spectrum_list = []
                for curator_h_spectrum in curator_entry['h_nmr']['spectrum']:
                    new_h_spectrum_entry = self.get_empty_h_spectrum_from_schema()
                    new_h_spectrum_entry['shift'] = curator_h_spectrum['shift']
                    new_h_spectrum_entry['multiplicity'] = curator_h_spectrum['multiplicity']
                    new_h_spectrum_entry['coupling'] = curator_h_spectrum['coupling']
                    new_h_spectrum_entry['atom_index'] = curator_h_spectrum['atom_index']
                    new_h_spectrum_entry['mol_block_index'] = curator_h_spectrum['rdkit_index']
                    new_h_spectrum_entry['interchangeable_index'] = curator_h_spectrum['interchangable_index']
                    new_spectrum_list.append(new_h_spectrum_entry)

                new_assignment_entry['h_nmr']['spectrum'] = new_spectrum_list
            else:
                final_status_dict['entries_with_no_h_nmr'] = True
            
            new_json['nmr_data']['assignment_data'].append(new_assignment_entry)
        
            # Validate json against schema
            try:
                jsonschema.validate(instance=new_json, schema=self.schema)
            except jsonschema.exceptions.ValidationError as e:
                final_status_dict['validation_error'] += (str(e) + "\n")
            
            final_json_list.append(new_json)
        
        return final_json_list, final_status_dict



