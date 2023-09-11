import sys
import json
from dateutil import parser

class JSONStandardizer:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.results = []
    
    def _standardize_deposition_system(self, json_data):
        submisison_date = json_data.get('submission', {}).get('submission_date', "")
        if submisison_date:
            json_data['submission']['submission_date'] = parser.parse(submisison_date).strftime('%Y-%m-%dT%H:%M:%S.%f+00:00')

        return json_data
    
    def _standardize_dft_team(self, json_data):
        return json_data
    
    def _standardize_wrapper(self, json_data):
        source = json_data.get('submission', {}).get('source', "")

        if source == "deposition_system":
            return self._standardize_deposition_system(json_data)
        elif source == "dft_team":
            return self._standardize_dft_team(json_data)
        else:
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
                standardized_json_list.append(self._standardize_wrapper(json_data))

            print("standardized_json_list is")
            print(standardized_json_list)
            
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
