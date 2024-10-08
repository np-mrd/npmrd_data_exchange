import json
import os
import pandas as pd
import jsonschema
import uuid

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
            print(f"Error decoding the JSON file: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def generate_empty_value(self, schema, empty_arrays=False):
        schema_type = schema.get("type")
        default_value = schema.get("default")
        
        if default_value is not None:
            return default_value
        elif schema_type == "object":
            return {key: self.generate_empty_value(value, empty_arrays) for key, value in schema.get("properties", {}).items()}
        elif schema_type == "array":
            if empty_arrays == True:
                print(f"empty_arrays toggle is {empty_arrays}")
            if empty_arrays == True:
                return []
            items_schema = schema.get("items")
            if isinstance(items_schema, list):
                return [self.generate_empty_value(item, empty_arrays) for item in items_schema]
            elif isinstance(items_schema, dict):
                return [self.generate_empty_value(items_schema, empty_arrays)] if items_schema else []
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

    def generate_json_from_schema(self):
        return self.generate_empty_value(self.schema)
    
    def generate_empty_json_from_schema(self):
        return self.generate_empty_value(schema=self.schema, empty_arrays=True)

    def get_empty_assignment_data_from_schema(self):
        return self.generate_empty_value(self.schema)['nmr_data']['assignment_data'][0]

    def get_empty_c_spectrum_from_schema(self):
        return self.generate_empty_value(self.schema)['nmr_data']['assignment_data'][0]['c_nmr']['spectrum'][0]
    
    def get_empty_h_spectrum_from_schema(self):
        return self.generate_empty_value(self.schema)['nmr_data']['assignment_data'][0]['h_nmr']['spectrum'][0]

    def convert_json(self):
        """Update the schema with data from the input JSON."""
        final_json_list = []

        # Iterate through full input json
        for curator_entry in self.curator_json_dict:
            new_json = self.generate_empty_json_from_schema()
            print("new_json is")
            print(new_json)

            new_json['compound_name'] = curator_entry['name']
            new_json['np_mrd_id'] = None
            new_json['smiles'] = curator_entry['smiles']
            new_json['citation']['doi'] = curator_entry['origin_doi']
            new_json['origin']['genus'] = curator_entry['origin_genus']
            new_json['origin']['species'] = curator_entry['origin_species']
            new_json['submission']['source'] = "npmrd_curator"
            new_json['nmr_data']['experimental_data']['nmr_metadata'] = []
            new_json['nmr_data']['peak_lists'] = []
            new_json['submission']['source'] = "npmrd_curator"
            
            # Entries to fill out the "assignment_data" list of the exchange json with.
            # Typically one for C and one for H
            new_assignment_entry = self.get_empty_assignment_data_from_schema()
            new_assignment_entry['curator_email_address'] = curator_entry['curator_email_address']
            new_assignment_entry['rdkit_version'] = curator_entry['rdkit_version']
            new_assignment_entry['mol_block'] = curator_entry['mol_block']
            
            new_assignment_uuid_c = str(uuid.uuid4())
            new_assignment_uuid_h = str(uuid.uuid4())
            
            if len(curator_entry['c_nmr']['spectrum']) > 0:
                new_assignment_entry['c_nmr']['assignment_uuid'] = new_assignment_uuid_c
                new_assignment_entry['c_nmr']['solvent'] = curator_entry['c_nmr']['solvent']
                new_assignment_entry['c_nmr']['temperature'] = curator_entry['c_nmr']['temperature']
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
                print(f"WARNING: NO c_nmr DATA IN ENTRY {curator_entry['name']} / {curator_entry['origin_doi']}")


            if len(curator_entry['h_nmr']['spectrum']) > 0:
                new_assignment_entry['h_nmr']['assignment_uuid'] = new_assignment_uuid_h
                new_assignment_entry['h_nmr']['solvent'] = curator_entry['h_nmr']['solvent']
                new_assignment_entry['h_nmr']['temperature'] = curator_entry['h_nmr']['temperature']
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
                    new_h_spectrum_entry['rdkit_index'] = curator_h_spectrum['rdkit_index']
                    new_h_spectrum_entry['interchangeable_index'] = curator_h_spectrum['interchangable_index']
                    new_spectrum_list.append(new_h_spectrum_entry)

                new_assignment_entry['h_nmr']['spectrum'] = new_spectrum_list
            
            new_json['nmr_data']['assignment_data'].append(new_assignment_entry)
            self.validate_exchange_json(new_json)
            
            final_json_list.append(new_json)
            
        return final_json_list
    
    def validate_exchange_json(self, json):
        try:
            jsonschema.validate(instance=json, schema=self.schema)
        except jsonschema.exceptions.ValidationError as e:
            # Print the validation error message
            print(f"Validation error: {e.message}")
            # Raise an exception to stop further execution
            raise e


