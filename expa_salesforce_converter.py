import logging
import lc_mapper


class InvalidEPException(Exception):
    pass


class EXPASalesforceConverter:
    def __init__(self):
        self.lc_owner_mapper = lc_mapper.LC2SFOwnerMapper()
        self.lc_city_mapper = lc_mapper.LC2CityMapper()

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

    def convert_expa_json_to_salesforce_dictionary(self, expa_json):
        logging.debug('Person JSON: %s: ', expa_json)
        result = {'FirstName': expa_json['first_name'], 'LastName': expa_json['last_name'],
                  'Email': expa_json['email']}
        logging.info('Loading %s %s (%s) from EXPA...', result['FirstName'], result['LastName'], result['Email'])
        if expa_json['current_office'] is not None:
            office_id = expa_json['current_office']['id']
        else:
            office_id = expa_json['home_lc']['id']
        if expa_json['cv_info'] is not None:
            result['EXPA_CV_URL__c'] = expa_json['cv_info']['url']
            result['EXPA_CV_Name__c'] = expa_json['cv_info']['name']
        try:
            result['OwnerId'] = self.lc_owner_mapper.op_to_sf(office_id)
            result['closest_city__c'] = self.lc_city_mapper.op_to_city(office_id)
        except KeyError:
            logging.error("The EP has an invalid current office: {0}".format(office_id))
        result['EXPA_ID__c'] = expa_json['id']
        result['EXPA_url__c'] = 'https://experience.aiesec.org/#/people/' + str(expa_json['id'])
        if expa_json['status'] is not None:
            result['EXPA_EP_Status__c'] = expa_json['status'].title()
        result['EXPA_SignUp_Date__c'] = expa_json['created_at']
        result['EXPA_Last_Interaction_Date__c'] = expa_json['updated_at']
        if expa_json['gender'] is not None:
            result['EXPA_Gender__c'] = expa_json['gender'].title()
        result['EXPA_Interviewed__c'] = expa_json['interviewed']
        if expa_json['profile'] is not None:
            person_json = expa_json['profile']
            result['EXPA_Programmes__c'] = ';'.join(EXPASalesforceConverter.get_programmes(person_json))
            result['EXPA_Minimum_Duration__c'] = person_json['duration_min']
            result['EXPA_Maximum_Duration__c'] = person_json['duration_max']
            result['EXPA_Earliest_Start_Date__c'] = person_json['earliest_start_date']
            result['EXPA_Latest_End_Date__c'] = person_json['latest_end_date']
            result['EXPA_Skills__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['skills'])
            result['EXPA_Languages__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['languages'])
            result['EXPA_Backgrounds__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['backgrounds'])
            result['EXPA_Issues__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['issues'])
            result['EXPA_Work_Fields__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['work_fields'])
            result['EXPA_Preferred_Organisations__c'] = EXPASalesforceConverter.collect_from_picklist(
                person_json['preferred_organisations'])
            result['EXPA_Preferred_Locations__c'] = EXPASalesforceConverter.collect_from_picklist(
                person_json['preferred_locations_info'])
        return result