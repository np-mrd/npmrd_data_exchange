import json
import argparse
import os
import pandas as pd
import uuid
import jsonschema

# How to run from command line
# python process_json.py input.json json_schema/npmrd-exchange_schema.json output.json
# Arguments:
#   input.json: The path to the input JSON file.
#   json_schema/npmrd-exchange_schema.json: The path to the JSON schema file.
#   uuid_json.xls: A spreadsheet used to keep track of assigned UUID values for each assignment data entry
#   output.json: The path to save the updated JSON file.


class CuratorConverter:
    def __init__(self, schema_file, input_file, assignment_uuid_spreadsheet_file, output_file):
        self.schema_file = schema_file
        self.input_file = input_file
        self.assignment_uuid_spreadsheet_file = assignment_uuid_spreadsheet_file
        self.output_file = output_file
        self.schema = self.load_json(schema_file)
        self.input_json = self.load_json(input_file)
        self.assignment_uuid_spreadsheet = self.load_spreadsheet(assignment_uuid_spreadsheet_file)

    @staticmethod
    def load_json(file_path):
        """Load JSON data from a file."""
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"The file at {file_path} was not found.")
        except json.JSONDecodeError:
            print("Error decoding the JSON file.")
        except Exception as e:
            print(f"An error occurred: {e}")

    @staticmethod
    def save_json(data, file_path):
        """Save JSON data to a file."""
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def load_spreadsheet(file_path):
        """Load spreadsheet data from a CSV file into a Pandas DataFrame."""
        try:
            df = pd.read_csv(file_path)
            return df
        except FileNotFoundError:
            print(f"The file at {file_path} was not found.")
        except pd.errors.EmptyDataError:
            print(f"The file at {file_path} is empty.")
        except pd.errors.ParserError:
            print(f"Error parsing the file '{file_path}'")
        except Exception as e:
            print(f"An error occurred: {e}")

    @staticmethod
    def save_spreadsheet(data, file_path):
        """Save DataFrame data to a CSV file."""
        data.to_csv(file_path, index=False)

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

    def generate_json_from_schema(self):
        return self.generate_empty_value(self.schema)

    def get_empty_assignment_data_from_schema(self):
        return self.generate_empty_value(self.schema)['nmr_data']['assignment_data'][0]

    def get_empty_spectrum_from_schema(self):
        return self.generate_empty_value(self.schema)['nmr_data']['assignment_data'][0]['spectrum'][0]

    def build_final_json(self):
        """Update the schema with data from the input JSON."""
        final_json_list = []

        # Iterate through full input json
        for curator_entry in self.input_json:
            new_json = self.generate_json_from_schema()

            new_json['compound_name'] = curator_entry['name']
            new_json['np_mrd_id'] = None
            new_json['smiles'] = curator_entry['smiles']
            new_json['citation']['doi'] = curator_entry['origin_doi']
            new_json['origin']['genus'] = curator_entry['origin_genus']
            new_json['origin']['species'] = curator_entry['origin_species']
            new_json['submission']['source'] = "npmrd_curator"

            has_assignment_data = False
            
            # Entries to fill out the "assignment_data" list of the exchange json with.
            # Typically one for C and one for H
            new_assignment_entry_list = []

            # Add carbon nmr values if they exist
            if len(curator_entry['c_nmr']['spectrum']) > 0:
                has_assignment_data = True
                new_assignment_entry = self.get_empty_assignment_data_from_schema()
                new_assignment_entry['assignment_uuid'] = self.determine_assignment_uuid(
                    curator_entry['smiles'],
                    curator_entry['origin_doi'],
                    "C"
                )
                new_assignment_entry['nucleus'] = "C"
                new_assignment_entry['solvent'] = curator_entry['c_nmr']['solvent']
                new_assignment_entry['temperature'] = curator_entry['c_nmr']['temperature']
                new_assignment_entry['temperature_units'] = "K"
                new_assignment_entry['reference'] = curator_entry['c_nmr']['reference']
                new_assignment_entry['frequency'] = curator_entry['c_nmr']['frequency']
                new_assignment_entry['frequency_units'] = "MHz"

                new_spectrum_list = []
                for curator_c_spectrum in curator_entry['c_nmr']['spectrum']:
                    new_spectrum_entry = self.get_empty_spectrum_from_schema()
                    print("H empty get_empty_assignment_data_from_schema is", new_spectrum_entry)
                    new_spectrum_entry['shift'] = curator_c_spectrum['shift']
                    new_spectrum_entry['atom_index'] = curator_c_spectrum['atom_index']
                    new_spectrum_entry['rdkit_index'] = [curator_c_spectrum['rdkit_index']]
                    new_spectrum_list.append(new_spectrum_entry)

                new_assignment_entry['spectrum'] = new_spectrum_list
                new_assignment_entry_list.append(new_assignment_entry)
            else:
                print(f"WARNING: NO c_nmr DATA IN ENTRY {curator_entry['name']} / {curator_entry['origin_doi']}")

            # Add hydrogen nmr values if they exist
            if len(curator_entry['h_nmr']['spectrum']) > 0:
                has_assignment_data = True
                new_assignment_entry = self.get_empty_assignment_data_from_schema()
                
                new_assignment_entry['assignment_uuid'] = self.determine_assignment_uuid(
                    curator_entry['smiles'],
                    curator_entry['origin_doi'],
                    "H"
                )
                new_assignment_entry['nucleus'] = "H"
                new_assignment_entry['solvent'] = curator_entry['h_nmr']['solvent']
                new_assignment_entry['temperature'] = curator_entry['h_nmr']['temperature']
                new_assignment_entry['temperature_units'] = "K"
                new_assignment_entry['reference'] = curator_entry['h_nmr']['reference']
                new_assignment_entry['frequency'] = curator_entry['h_nmr']['frequency']
                new_assignment_entry['frequency_units'] = "MHz"

                new_spectrum_list = []
                for curator_h_spectrum in curator_entry['h_nmr']['spectrum']:
                    new_spectrum_entry = self.get_empty_spectrum_from_schema()
                    print("H empty get_empty_assignment_data_from_schema is", new_spectrum_entry)
                    new_spectrum_entry['shift'] = curator_h_spectrum['shift']
                    new_spectrum_entry['multiplicity'] = curator_h_spectrum['multiplicity']
                    new_spectrum_entry['coupling'] = curator_h_spectrum['coupling']
                    new_spectrum_entry['atom_index'] = curator_h_spectrum['atom_index']
                    new_spectrum_entry['rdkit_index'] = curator_h_spectrum['rdkit_index']
                    new_spectrum_entry['interchangeable_index'] = curator_h_spectrum['interchangable_index']
                    new_spectrum_list.append(new_spectrum_entry)

                new_assignment_entry['spectrum'] = new_spectrum_list
                
                # Validate the json with the schema
                new_assignment_entry_list.append(new_assignment_entry)
            else:
                print(f"WARNING: NO h_nmr DATA IN ENTRY {curator_entry['name']} / {curator_entry['origin_doi']}")

            # Attach assignment data to full NP-MRD Json
            if has_assignment_data:
                new_json['nmr_data']['assignment_data'] = new_assignment_entry_list

                # Validate assignment entry
                self.validate_exchange_json(new_json)
                
                final_json_list.append(new_json)
            else:
                print(f"WARNING: NO ASSIGNMENT DATA IN ENTRY {curator_entry['name']} / {curator_entry['origin_doi']}")

        return final_json_list

    def determine_assignment_uuid(self, smiles, doi, nucleus):
        """Determine or generate assignment UUIDs for a list."""
        result_uuids = []

        match = self.assignment_uuid_spreadsheet[
            (self.assignment_uuid_spreadsheet['smiles'] == smiles) &
            (self.assignment_uuid_spreadsheet['doi'] == doi) &
            (self.assignment_uuid_spreadsheet['nucleus'] == nucleus)
        ]

        if match.empty:
            assignment_uuid = str(uuid.uuid4())

            new_spreadsheet_entry = pd.DataFrame({
                'smiles': [smiles],
                'doi': [doi],
                'nucleus': [nucleus],
                'assignment_uuid': assignment_uuid
            })

            self.assignment_uuid_spreadsheet = pd.concat([
                self.assignment_uuid_spreadsheet,
                new_spreadsheet_entry
            ], ignore_index=True)
            
        else:
            assignment_uuid = match.iloc[0]['assignment_uuid']

        return assignment_uuid
    
    def validate_exchange_json(self, json):
        try:
            jsonschema.validate(instance=json, schema=self.schema)
            print("Validation successful. Data conforms to schema.")
        except jsonschema.exceptions.ValidationError as e:
            # Print the validation error message
            print(f"Validation error: {e.message}")
            # Raise an exception to stop further execution
            raise e
        
    def convert_json(self):
        updated_data = self.build_final_json()
        self.save_spreadsheet(self.assignment_uuid_spreadsheet, self.assignment_uuid_spreadsheet_file)
        self.save_json(updated_data, self.output_file)
        print(f"-- Generated Exchange JSON: '{self.output_file}'")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a JSON file and update schema.')
    parser.add_argument('input_file', type=str, help='The path to the input JSON file.')
    parser.add_argument('schema_file', type=str, help='The path to the JSON schema file.')
    parser.add_argument('assignment_uuid_spreadsheet_file', type=str, help='The path to the assignment uuid master list spreadsheet.')
    parser.add_argument('output_file', type=str, help='The path to save the updated JSON file.')

    args = parser.parse_args()

    curator_converter = CuratorConverter(
        args.schema_file,
        args.input_file,
        args.assignment_uuid_spreadsheet_file,
        args.output_file
    )
    curator_converter.convert_json()