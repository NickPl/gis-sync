# coding=utf-8

import simple_salesforce
from simple_salesforce import SalesforceMalformedRequest
import logging


class SalesforceWrapper:
    def __init__(self, _email, _password, _security_token, _sandbox):
        self.sf = simple_salesforce.Salesforce(username=_email, password=_password, security_token=_security_token,
                                               sandbox=_sandbox)
        self.current_lead_ids = []
        self.current_ep_ids = []

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
            if query_result is None or query_result["totalSize"] == 0:
                return False
            else:
                self.current_lead_ids = []
                for record in query_result["records"]:
                    self.current_lead_ids.append(record["Id"])
                return True
        except Exception:
            logging.exception('An error has occured while searching for Salesforce leads!')

    def does_account_exist(self, email):
        try:
            query = 'FIND {' + self.escape_query_argument(email) + '} IN EMAIL FIELDS RETURNING Account'
            query_result = self.sf.search(query)
            return query_result is not None
        except Exception:
            logging.exception('An error has occured while searching for Salesforce accounts!')

    def does_ep_exist(self, email, expa_id):
        query = "SELECT Id FROM EP__c WHERE E_Mail__c = '{0}' OR EXPA_ID__c = {1}".format(
            email, expa_id)
        try:
            query_result = self.sf.query_all(query)
            if query_result is None or query_result["totalSize"] == 0:
                return False
            else:
                self.current_ep_ids = []
                for record in query_result["records"]:
                    self.current_ep_ids.append(record["Id"])
                return True
        except Exception:
            logging.exception('An error has occured while searching for Salesforce EPs!')

    def create_lead(self, profile_dictionary):
        profile_dictionary['RecordTypeId'] = '01220000000MHoeAAG'
        profile_dictionary['LeadSource'] = 'Opportunities Portal'
        self.sf.Lead.create(profile_dictionary)

    def update_lead(self, profile_dictionary):
        for record in self.current_lead_ids:
            try:
                self.sf.Lead.update(record, profile_dictionary)
            except SalesforceMalformedRequest as smr:
                logging.warning(smr)

    def update_ep(self, profile_dictionary):
        profile_dictionary.pop("FirstName", None)
        profile_dictionary.pop("LastName", None)
        profile_dictionary.pop("Email", None)
        profile_dictionary.pop("OwnerId", None)
        for record in self.current_ep_ids:
            try:
                self.sf.EP__c.update(record, profile_dictionary)
            except SalesforceMalformedRequest as smr:
                logging.warning(smr)
