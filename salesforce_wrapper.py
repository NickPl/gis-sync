# coding=utf-8

import simple_salesforce
import json


class SalesforceWrapper:
    def __init__(self, _email, _password, _security_token, _sandbox):
        self.sf = simple_salesforce.Salesforce(username=_email, password=_password, security_token=_security_token,
                                               sandbox=_sandbox)
        self.current_lead_id = 0
        self.current_account_id = 0
        self.current_ep_ids = []

    @staticmethod
    def escape_query_argument(query_argument):
        return query_argument.replace("?", r"\?").replace("&", r"\&").replace("|", r"\|").replace("!", r"\!").replace(
            "{", r"\{").replace("}", r"\}").replace("^", r"\^").replace("$", r"\$").replace("*", r"\*").replace("+",
                                                                                                                r"\+").replace(
            "-", r"\-").replace("~", r"\~").replace("'", r"\'").replace('"', r'\"').replace('\\', r'\\\\')

    def does_lead_exist(self, email):
        query = 'FIND {' + self.escape_query_argument(email) + '} IN EMAIL FIELDS RETURNING LEAD'
        query_result = self.sf.search(query)
        if query_result is None:
            return False
        else:
            self.current_lead_id = str(query_result[0]['Id'])
            return True

    def does_account_exist(self, email):
        query = 'FIND {' + self.escape_query_argument(email) + '} IN EMAIL FIELDS RETURNING ACCOUNT'
        query_result = self.sf.search(query)
        if query_result is None:
            return False
        else:
            self.current_account_id = str(query_result[0]['Id'])
            return True

    def does_ep_exist(self, email):
        query = "SELECT Id FROM EP__c WHERE E_Mail__c = '{0}'".format(email)
        query_result = self.sf.query_all(query)
        if query_result is None or query_result["totalSize"] == 0:
            return False
        else:
            self.current_ep_ids = []
            for record in query_result["records"]:
                self.current_ep_ids.append(record["Id"])
            return True

    def create_lead(self, profile_dictionary):
        profile_dictionary['RecordTypeId'] = '01220000000MHoeAAG'
        profile_dictionary['LeadSource'] = 'Opportunities Portal'
        self.sf.Lead.create(profile_dictionary)

    def update_lead(self, profile_dictionary):
        self.sf.Lead.update(self.current_lead_id, profile_dictionary)

    def update_ep(self, profile_dictionary):
        profile_dictionary.pop("FirstName", None)
        profile_dictionary.pop("LastName", None)
        profile_dictionary.pop("Email", None)
        profile_dictionary.pop("OwnerId", None)
        for record in self.current_ep_ids:
            self.sf.EP__c.update(record, profile_dictionary)
