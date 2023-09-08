import sys
import json
import re


class JSONValidator:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.results = []

    def _check_if_entry_is_valid(self, result):
        """
        Checks if a provided result dictionary has had it's "valid" value set to false
        and sets it to True if it hasn't. Intended to be run as a final check in validaiton.
        """
        if result['valid'] != False:
            result['valid'] = True
        return result

    def _fail_entry(self, result, error_message):
        """
        Causes a provided result dictionary to be set to false and appends the provided
        error_message to the result's "error_message" value.
        """
        result['valid'] = False
        if type(result['error_message']) == str:
            result['error_message'] = result['error_message'] + \
                ". " + error_message
        else:
            result['error_message'] = error_message

        return result

    def _confirm_non_null_fields(self, json, result, field_names):
        """
        Used to confirm that a provided list of field_names is present and not null within the
        individual compound json provided to it. field_names is a list of stings.
        Nested values can be represented like such "nest.nested_value1.nested_value2".
        Can also be used to check if one of a list of provided entries clears this condition
        by providing multiple entries as a single string separated by a "|" like such:
        "nest.nested_valueA1.nested_valueA2|nest2.nested_valueB1.nested_valueB2.
        
        Args:
            json (dict): NP-MRD Exchange json for a single compound
            result (dict): Result dictionary for a compound
            field_names (list): A list of field names that will be checked for in the
            json to confirm that they exist and are non-null.

        Returns:
            dict: dictionary status report for the compound json passed into it (see 
            validate returns for details).
        """
        for field_name in field_names:
            # Split "|" statement in case we are looking for one of x fields
            field_one_ofs = field_name.split('|')
            num_fails = 0
            fail_threshold = len(field_one_ofs)
            for one_of in field_one_ofs:
                # Now traverse nested entries specified in field name
                current_data = json
                field_parts = one_of.split('.')
                for part in field_parts:
                    if part in current_data and current_data[part] != None:
                        current_data = current_data[part]
                    else:
                        num_fails += 1
                        if num_fails == fail_threshold:
                            error_message = field_name + " is not in json or is null"
                            result = self._fail_entry(result, error_message)

        return result

    def _check_deposition_system(self, json, result):
        """
        Runs validation steps necessary for a compound with the submission.source "deposition_system" 
        """
        if json['submission']['source'] != "deposition_system":
            self._fail_entry(
                result, "Invalid source for deposition_system: " + json['submission']['source'])

        always_non_null = [
            'smiles',
            'inchikey',
            'submission.type',
            'submission.uuid',
            'submission.compound_uuid',
            'submission.submission_date',
            'submission.embargo_status',
            'depositor_info.email',
            'depositor_info.show_email_in_attribution',
            'depositor_info.show_name_in_attribution',
            'depositor_info.show_organization_in_attribution',
            'depositor_info.account_id',
        ]
        result = self._confirm_non_null_fields(json, result, always_non_null)

        # Ensure published article has necessary fields
        if json['submission']['type'] == "published_article":
            non_null_citation = ['citation.doi|citation.pmid|citation.pii']
            result = self._confirm_non_null_fields(
                json, result, non_null_citation)
        elif json['submission']['type'] == "presubmission_article":
            pass
        elif json['submission']['type'] == "private_deposition":
            non_null_compound_source = [
                'origin.private_collection.compound_source_type']
            result = self._confirm_non_null_fields(
                json, result, non_null_compound_source)
            compound_source_type = json.get('origin', {}).get(
                'private_collection', {}).get('compound_source_type', "")
            if compound_source_type == "purified_in_house":
                non_null_purified_in_house = [
                    'compound_name',
                    'origin.species',
                    'origin.genus',
                ]
                result = self._confirm_non_null_fields(
                    json, result, non_null_purified_in_house)
            elif compound_source_type == "commercial":
                non_null_commerical = [
                    'origin.private_collection.commercial.supplier',
                    'origin.private_collection.commercial.cas_number'
                ]
                result = self._confirm_non_null_fields(
                    json, result, non_null_commerical)
            elif compound_source_type == "compound_library":
                non_null_compound_library = [
                    'origin.private_collection.compound_library.library_name'
                ]
                result = self._confirm_non_null_fields(
                    json, result, non_null_compound_library)
            elif compound_source_type == "other":
                non_null_other = [
                    'origin.private_collection.other.user_specified_compound_source',
                    'compound_name',
                    'origin.species',
                    'origin.genus',
                ]
                result = self._confirm_non_null_fields(
                    json, result, non_null_other)

        if json['submission']['embargo_status'] == "publish":
            pass
        elif json['submission']['embargo_status'] == "embargo_until_date":
            non_null_embargo_date = ['submission.embargo_date']
            result = self._confirm_non_null_fields(
                json, result, non_null_embargo_date)
        elif json['submission']['embargo_status'] == "embargo_until_publication":
            pass

        if json['depositor_info']['show_name_in_attribution'] == True:
            result = self._confirm_non_null_fields(
                json, result, ['depositor_info.attribution_name'])
        if json['depositor_info']['show_organization_in_attribution'] == True:
            result = self._confirm_non_null_fields(
                json, result, ['depositor_info.attribution_organization'])

        # If test has not failed then pass back positive result
        return self._check_if_entry_is_valid(result)

    def _check_dft_team(self, json, result):
        """
        Runs validation steps necessary for a compound with the submission.source "dft_team" 
        """
        
        return self._check_if_entry_is_valid(result)

    def _check_general(self, json):
        """
        Validates that a valid submission.source exists in the json for an individual
        compound. Then runs an additional check script to validate the json depending
        on its source.
        
        Args:
            json (dict): json for individual compound in the NP-MRD Exchange json format.

        Returns:
            dict: dictionary status report for the compound json passed into it (see 
            validate returns for details).
        """
        source = json.get('submission', {}).get('source', "")
        result = {
            'index': None,
            'inchikey': json.get('inchikey', ""),
            'source': source,
            "type": json.get('submission', {}).get('type', ""),
            'valid': None,
            'error_message': None,
        }

        if source == "deposition_system":
            return self._check_deposition_system(json, result)
        elif source == "dft_team":
            return self._check_dft_team(json, result)
        else:
            return self._fail_entry(result, "Invalid source")

    def validate(self):
        """
        Used to run the validation of an NP-MRD Exchange JSON. Returns a list of
        dictionaries with the results of the validation.

        Returns:
            list: Returns a list of dictionaries, each acting as a status
            report one of the compounds in the input json. These fields include
            (for each compound)...
                index (int): the index of the compound in the input json list 
                inchikey (str): the inchikey of the compound in the input json
                source (str): the "submission.source" value in the input json
                type (str): the "submission.type" value in the json
                valid (bool): whether or not that compound was found to be valid
                error_message (str): if the compound is not valid this will include
                message as to why.

        Example Output:
            [
                {
                    'index': 0,
                    'inchikey': 'NJPYVCPTFPPLNC-UHFFFAOYSA-N',
                    'source': 'deposition_system',
                    'type': 'published_article',
                    'valid': True,
                    'error_message': None
                }, 
                {
                    'index': 1,
                    'inchikey': 'PRMUPNPVIWOFLN-UHFFFAOYSA-N',
                    'source': 'deposition_system',
                    'type': 'published_article',
                    'valid': True,
                    'error_message': None
                }
            ]
        """
        try:
            with open(self.json_file_path, 'r') as file:
                json_list = json.load(file)

            for i, json_data in enumerate(json_list):
                validation_result = self._check_general(json_data)
                validation_result['index'] = i
                self.results.append(validation_result)

            print("results is")
            print(self.results)

            return self.results

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
        validator = JSONValidator(json_file_path)
        if validator.validate():
            print("All entries passed validation.")
        else:
            print("Some entries failed validation.")
