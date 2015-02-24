import requests
import expa_account
import datetime
import lc_mapper
import logging


class EXPAWrapper:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://gis-api.aiesec.org:443/v1/'
        self.people_url = self.base_url + 'people/'
        self.lc_mapper = lc_mapper.LCMapper()

    def get_page_number(self, last_interaction=None):
        url = self.base_url + 'people.json?access_token=' + self.access_token + '&per_page=200'
        if last_interaction is not None:
            url += '&filters%5Blast_interaction%5D%5Bfrom%5D=' + str(last_interaction)
        current_page = requests.get(url, verify=False).json()
        return current_page['paging']['total_pages']

    def get_all_records(self, last_interaction=None, page=None):
        url = self.base_url + 'people.json?access_token=' + self.access_token + '&per_page=200'
        if last_interaction is not None:
            url += '&filters%5Blast_interaction%5D%5Bfrom%5D=' + str(last_interaction)
        current_page = requests.get(url, verify=False).json()
        logging.debug('Current page from EXPA: {0}'.format(current_page))
        total_items = current_page['paging']['total_items']
        logging.info('Loading %d EPs from EXPA...', total_items)
        total_pages = current_page['paging']['total_pages']
        result = []
        if page is None:
            for c in range(1, total_pages + 1):
                current_page = requests.get(url + '&page=%d' % c, verify=False).json()
                for i in current_page['data']:
                    current_id = i['id']
                    person = self.get_person_detail(current_id)
                    date_created = datetime.datetime.strptime(i['created_at'], "%Y-%m-%dT%H:%M:%SZ").date()
                    result.append(expa_account.EXPAAccount(i['first_name'] + ' ' + i['last_name'], i['email'], i['id'], date_created,
                                                           self.get_profile_dictionary(person)))
        else:
            current_page = requests.get(url + '&page=%d' % page, verify=False).json()
            for i in current_page['data']:
                current_id = i['id']
                person = self.get_person_detail(current_id)
                date_created = datetime.datetime.strptime(i['created_at'], "%Y-%m-%dT%H:%M:%SZ").date()
                result.append(expa_account.EXPAAccount(i['first_name'] + ' ' + i['last_name'], i['email'], i['id'], date_created,
                                                        self.get_profile_dictionary(person)))

        return result

    def get_person_detail(self, person_id):
        url = self.people_url + str(person_id) + '.json?access_token=' + self.access_token
        return requests.get(url, verify=False).json()

    @staticmethod
    def get_programmes(person_json):
        programmes = []
        for i in person_json['selected_programmes_info']:
            programmes.append(i['short_name'])
        return programmes

    @staticmethod
    def collect_from_picklist(json):
        result = []
        for i in json:
            result.append(i['name'].title())
        return ', '.join(result)

    def get_profile_dictionary(self, person_json):
        result = {'FirstName': person_json['first_name'], 'LastName': person_json['last_name'],
                  'Email': person_json['email']}
        logging.info('Loading %s %s (%s) from EXPA...', result['FirstName'], result['LastName'], result['Email'])
        logging.debug('Person JSON: %s: ', person_json)
        if person_json['current_office'] is not None:
            office_id = person_json['current_office']['id']
        else:
            office_id = person_json['home_lc']['id']
        result['OwnerId'] = self.lc_mapper.op_to_sf(office_id)
        result['EXPA_ID__c'] = person_json['id']
        result['EXPA_url__c'] = 'https://experience.aiesec.org/#/people/' + str(person_json['id'])
        if person_json['status'] is not None:
            result['EXPA_EP_Status__c'] = person_json['status'].title()
        result['EXPA_SignUp_Date__c'] = person_json['created_at']
        result['EXPA_Last_Interaction_Date__c'] = person_json['updated_at']
        if person_json['gender'] is not None:
            result['EXPA_Gender__c'] = person_json['gender'].title()
        result['EXPA_Interviewed__c'] = person_json['interviewed']
        if person_json['profile'] is not None:
            person_json = person_json['profile']
            result['EXPA_Programmes__c'] = ';'.join(self.get_programmes(person_json))
            result['EXPA_Minimum_Duration__c'] = person_json['duration_min']
            result['EXPA_Maximum_Duration__c'] = person_json['duration_max']
            result['EXPA_Earliest_Start_Date__c'] = person_json['earliest_start_date']
            result['EXPA_Latest_End_Date__c'] = person_json['latest_end_date']
            result['EXPA_Skills__c'] = self.collect_from_picklist(person_json['skills'])
            result['EXPA_Languages__c'] = self.collect_from_picklist(person_json['languages'])
            result['EXPA_Backgrounds__c'] = self.collect_from_picklist(person_json['backgrounds'])
            result['EXPA_Issues__c'] = self.collect_from_picklist(person_json['issues'])
            result['EXPA_Work_Fields__c'] = self.collect_from_picklist(person_json['work_fields'])
            result['EXPA_Preferred_Organisations__c'] = self.collect_from_picklist(
                person_json['preferred_organisations'])
            result['EXPA_Preferred_Locations__c'] = self.collect_from_picklist(person_json['preferred_locations_info'])
        return result

