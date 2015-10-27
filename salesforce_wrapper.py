# coding=utf-8

import simple_salesforce
from simple_salesforce import SalesforceMalformedRequest
import logging


class SalesforceWrapper:
    def __init__(self, _email, _password, _security_token, _sandbox):
        self.sf = simple_salesforce.Salesforce(username=_email, password=_password, security_token=_security_token,
                                               sandbox=_sandbox)
        self.sf.headers['Sforce-Auto-Assign'] = 'FALSE'
        self.current_lead_ids = []
        self.current_account_ids = []
        self.current_opportunity_ids = []

    @staticmethod
    def escape_query_argument(query_argument):
        escaped_argument = query_argument.replace("'", r"\'").replace('"', r'\"').replace('\\', r'\\\\').replace("?",
                                                                                                                 r"\?").replace(
            "&", r"\&").replace("|", r"\|").replace("!", r"\!").replace("^", r"\^").replace("$", r"\$").replace("*",
                                                                                                                r"\*").replace(
            "+", r"\+").replace("-", r"\-").replace("~", r"\~")
        logging.debug("Escaping {0} to {1}...".format(query_argument, escaped_argument))
        return escaped_argument

    def does_lead_exist(self, email, expa_id):
        query = "SELECT Id FROM Lead WHERE RecordTypeId = '{0}' AND (Email = '{1}' OR EXPA_ID__c = {2})".format(
            '01220000000MHoeAAG', email, expa_id)
        try:
            query_result = self.sf.query_all(query)
            if self.is_query_result_empty(query_result):
                return False
            else:
                self.current_lead_ids = []
                for record in query_result["records"]:
                    self.current_lead_ids.append(record["Id"])
                return True
        except Exception:
            logging.exception('An error has occured while searching for Salesforce leads!')

    def does_account_exist(self, email, expa_id=None):
        query = "SELECT Id FROM Account WHERE PersonEmail = '{0}'".format(email)
        if expa_id is not None:
            query += " OR EXPA_ID__c = {0}".format(expa_id)
        try:
            query_result = self.sf.query_all(query)
            if self.is_query_result_empty(query_result):
                return False
            else:
                self.current_account_ids = []
                for record in query_result["records"]:
                    self.current_account_ids.append(record["Id"])
                return True
        except Exception:
            logging.exception('An error has occured while searching for Salesforce accounts!')

    def does_opportunity_exist(self, expa_id):
        query = "SELECT Id FROM TN__c WHERE Opportunity_ID__c = {0}".format(expa_id)
        try:
            query_result = self.sf.query_all(query)
            if self.is_query_result_empty(query_result):
                return False
            else:
                self.current_opportunity_ids = []
                for record in query_result["records"]:
                    self.current_opportunity_ids.append(record["Id"])
                    return True
        except Exception:
            logging.exception('An error has occured while searching for Salesforce opportunities!')

    @staticmethod
    def is_query_result_empty(query_result):
        return query_result is None or query_result["totalSize"] == 0

    def create_account(self, profile_dictionary):
        result = self.sf.Account.create(profile_dictionary)
        return result['id']

    def create_lead(self, profile_dictionary):
        result = self.sf.Lead.create(profile_dictionary)
        return result['id']

    def update_lead(self, profile_dictionary):
        for record in self.current_lead_ids:
            try:
                self.sf.Lead.update(record, profile_dictionary)
            except SalesforceMalformedRequest as smr:
                logging.warning(smr)

    def update_account(self, profile_dictionary):
        profile_dictionary.pop("FirstName", None)
        profile_dictionary.pop("LastName", None)
        profile_dictionary.pop("Email", None)
        profile_dictionary.pop("OwnerId", None)
        profile_dictionary.pop("closest_city__c", None)
        profile_dictionary.pop("Minimum_Duration_of_Internship__c", None)
        profile_dictionary.pop("Maximum_Duration_of_Internship__c", None)
        profile_dictionary.pop("EXPA_SignUp_Date__c", None)
        profile_dictionary.pop("Area_of_world_interested_in_going__c", None)
        profile_dictionary.pop("specific_countries__c", None)
        for record in self.current_account_ids:
            try:
                self.sf.Account.update(record, profile_dictionary)
            except SalesforceMalformedRequest as smr:
                logging.warning(smr)

    def update_opportunity(self, opportunity_dictionary):
        for record in self.current_opportunity_ids:
            try:
                self.sf.TN__c.update(record, opportunity_dictionary)
                return record
            except SalesforceMalformedRequest as smr:
                logging.warning(smr)

    def create_opportunity(self, opportunity_dictionary):
        result = self.sf.TN__c.create(opportunity_dictionary)
        return result['id']

    def get_applicants(self, opportunity_id):
        result = []
        query = "SELECT Id, EXPA_EP_ID__c FROM Account WHERE Opportunity__c = '{0}'".format(opportunity_id)
        try:
            query_result = self.sf.query_all(query)
            if not self.is_query_result_empty(query_result):
                for record in query_result["records"]:
                    result.append(record["EXPA_EP_ID__c"])
            return result
        except Exception:
            logging.exception('An error has occured while searching for Salesforce trainees!')

    def does_match_object_exist(self, opportunity_id):
        query = "SELECT Id FROM Match2__c WHERE Opportunity__c = '{0}'".format(opportunity_id)
        try:
            query_result = self.sf.query_all(query)
            return not self.is_query_result_empty(query_result)
        except Exception:
            logging.exception('An error has occured while searching for Salesforce match objects!')
            return False

    def update_match_object(self, opportunity_id, match_data):
        query = "SELECT Id FROM Match2__c WHERE Opportunity__c = '{0}'".format(opportunity_id)
        try:
            query_result = self.sf.query_all(query)
            for record in query_result["records"]:
                match_dictionary = {"Match_Date__c": match_data['matched_date']}
                if match_data['realized_date'] is not None:
                    match_dictionary['Realized_Date__c'] = match_data['realized_date']
                self.sf.Match2__c.update(record['Id'], match_dictionary)
        except Exception:
            logging.exception('An error has occured while creating a Salesforce match object!')

    def create_match_object(self, opportunity_id, match_data):
        query = "SELECT Id FROM Account WHERE Opportunity__c = '{0}' AND EXPA_EP_ID__c = {1}".format(opportunity_id, match_data['person'])
        try:
            query_result = self.sf.query_all(query)
            for record in query_result["records"]:
                account_id = record['Id']
            match_dictionary = {"Trainee__c": account_id, "Opportunity__c": opportunity_id, "Match_Date__c": match_data['matched_date']}
            if 'realized_date' in match_data:
                match_dictionary['Realized_Date__c'] = match_data['realized_date']
            self.sf.Match2__c.create(match_dictionary)
        except Exception:
            logging.exception('An error has occured while creating a Salesforce match object!')


