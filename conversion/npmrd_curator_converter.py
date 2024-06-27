import json
import argparse
import os

# How to run from command line
# python process_json.py input.json json_schema/npmrd-exchange_schema.json output.json
# Arguments:
#   input.json: The path to the input JSON file.
#   json_schema/npmrd-exchange_schema.json: The path to the JSON schema file.
#   output.json: The path to save the updated JSON file.


def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_json(data, file_path):
    """Save JSON data to a file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def generate_empty_value(schema):
    schema_type = schema.get("type")

    if schema_type == "object":
        return {key: generate_empty_value(value) for key, value in schema.get("properties", {}).items()}

    elif schema_type == "array":
        items_schema = schema.get("items")
        if isinstance(items_schema, list):
            return [generate_empty_value(item) for item in items_schema]
        elif isinstance(items_schema, dict):
            return [generate_empty_value(items_schema)]
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


def generate_json_from_schema(schema):
    return generate_empty_value(schema)

def get_empty_assignment_data_from_schema(schema):
    return generate_empty_value(schema)['nmr_data']['assignment_data'][0]

def get_empty_spectrum_from_schema(schema):
    return generate_empty_value(schema)['nmr_data']['assignment_data'][0]['spectrum'][0]


def build_final_json(schema, input_json):
    """Update the schema with data from the input JSON."""
    # Copy fields from input_json to schema
    final_json_list = []
    
    for curator_entry in input_json:
        # Create JSON and 
        new_json = generate_json_from_schema(schema)
        
        new_json['compound_name'] = curator_entry['name']
        new_json['np_mrd_id'] = None
        new_json['smiles'] = curator_entry['name']
        new_json['citation']['doi'] = curator_entry['origin_doi']
        # ??? = curator_entry['origin_type']
        new_json['origin']['genus'] = curator_entry['origin_genus']
        new_json['origin']['species'] = curator_entry['origin_species']
        
        has_assignment_data = False
        new_assignment_entry_list = []
        
        # Append C NMR Assignment
        if len(curator_entry['c_nmr']['spectrum']) > 0:
            has_assignment_data = True
            
            # Fill assignment_data fields
            new_assignment_entry = get_empty_assignment_data_from_schema(schema)
            new_assignment_entry['atom'] = "C"
            new_assignment_entry['solvent'] = curator_entry['c_nmr']['solvent']
            new_assignment_entry['temperature'] = curator_entry['c_nmr']['temperature']
            new_assignment_entry['temperature_units'] = "K"
            new_assignment_entry['reference'] = curator_entry['c_nmr']['reference']
            new_assignment_entry['frequency'] = curator_entry['c_nmr']['frequency']
            new_assignment_entry['frequency_units'] = "MHz"
            
            new_spectrum_list = []
            for curator_c_spectrum in curator_entry['c_nmr']['spectrum']:
                new_spectrum_entry = get_empty_spectrum_from_schema(schema)
                new_spectrum_entry['shift'] = curator_c_spectrum['shift']
                # new_spectrum_entry['integration'] = ???
                # new_spectrum_entry['multiplicity'] = None
                new_spectrum_entry['coupling'] = []
                new_spectrum_entry['atom_index'] = curator_c_spectrum['atom_index']
                new_spectrum_entry['rdkit_index'] = [curator_c_spectrum['rdkit_index']]
                new_spectrum_entry['interchangeable_index'] = []
                new_spectrum_list.append(new_spectrum_entry)
            
            new_assignment_entry['spectrum'] = new_spectrum_list
            new_assignment_entry_list.append(new_assignment_entry)
        else:
            print(f"WARNING: NO h_nmr DATA IN ENTRY {curator_entry['name']} / {curator_entry['origin_doi']}")              
                    
        # Append H NMR Assignment data
        if len(curator_entry['h_nmr']['spectrum']) > 0:
            has_assignment_data = True
            # Fill assignment_data fields
            new_assignment_entry = get_empty_assignment_data_from_schema(schema)
            new_assignment_entry['atom'] = "H"
            new_assignment_entry['solvent'] = curator_entry['h_nmr']['solvent']
            new_assignment_entry['temperature'] = curator_entry['h_nmr']['temperature']
            new_assignment_entry['temperature_units'] = "K"
            new_assignment_entry['reference'] = curator_entry['h_nmr']['reference']
            new_assignment_entry['frequency'] = curator_entry['h_nmr']['frequency']
            new_assignment_entry['frequency_units'] = "MHz"
            
            new_spectrum_list = []
            for curator_h_spectrum in curator_entry['h_nmr']['spectrum']:
                # Fill spectrum list
                new_spectrum_entry = get_empty_spectrum_from_schema(schema)
                new_spectrum_entry['shift'] = curator_h_spectrum['shift']
                # new_spectrum_entry['integration'] = ???
                new_spectrum_entry['multiplicity'] = curator_h_spectrum['multiplicity']
                new_spectrum_entry['coupling'] = curator_h_spectrum['coupling']
                new_spectrum_entry['atom_index'] = curator_h_spectrum['atom_index']
                new_spectrum_entry['rdkit_index'] = curator_h_spectrum['rdkit_index']
                new_spectrum_entry['interchangeable_index'] = curator_h_spectrum['interchangable_index']
                new_spectrum_list.append(new_spectrum_entry)
            
            new_assignment_entry['spectrum'] = new_spectrum_list
            new_assignment_entry_list.append(new_assignment_entry)
        else:
            print(f"WARNING: NO h_nmr DATA IN ENTRY {curator_entry['name']} / {curator_entry['origin_doi']}")
        
        if has_assignment_data:
            new_json['nmr_data']['assignment_data'] = new_assignment_entry_list
            final_json_list.append(new_json)
        else:
            print(f"WARNING: NO ASSIGNMENT DATA IN ENTRY {curator_entry['name']} / {curator_entry['origin_doi']}")
    
    return final_json_list


def main(input_file, schema_file, output_file):
    schema = load_json(schema_file)
    input_json = load_json(input_file)
    updated_data = build_final_json(schema, input_json)
    print(f"-- Generated Exchange JSON: '{output_file}'")
    save_json(updated_data, output_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a JSON file and update schema.')
    parser.add_argument('input_file', type=str, help='The path to the input JSON file.')
    parser.add_argument('schema_file', type=str, help='The path to the JSON schema file.')
    parser.add_argument('output_file', type=str, help='The path to save the updated JSON file.')
    
    args = parser.parse_args()
    main(args.input_file, args.schema_file, args.output_file)