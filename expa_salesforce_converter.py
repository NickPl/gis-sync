# coding=utf-8

import logging
import lc_mapper


class InvalidEPException(Exception):
    pass


class EXPASalesforceConverter:
    def __init__(self):
        self.lc_owner_mapper = lc_mapper.LC2SFOwnerMapper()
        self.lc_city_mapper = lc_mapper.LC2CityMapper()
        self.lc_sfname_mapper = lc_mapper.LC2SFAccountMapper()

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

    @staticmethod
    def collect_from_multipicklist(json):
        result = []
        for i in json:
            result.append(i['name'].title())
        return ';'.join(result)

    @staticmethod
    def collect_languages(json, required=True):
        result = []
        for i in json:
            if required and i['option'] == 'required' or not required and i['option'] != 'required':
                result.append(i['name'])
        return ';'.join(result)

    def convert_trainee_json_to_salesforce_dictionary(self, trainee_json, owner_id, opportunity_id):
        logging.debug('Trainee JSON: %s: ', trainee_json)
        result = {'FirstName': trainee_json['first_name'], 'LastName': trainee_json['last_name'],
                  'PersonEmail': trainee_json['email']}
        logging.info('Loading %s %s (%s) from EXPA...', result['FirstName'], result['LastName'], result['PersonEmail'])
        result['EXPA_EP_ID__c'] = trainee_json['id']
        if trainee_json['dob'] is not None and trainee_json['dob'][4] == '-':
            result['Birth_Date__c'] = trainee_json['dob']
        if trainee_json['gender'] is not None:
            result['Gender__c'] = trainee_json['gender'].title()
        if trainee_json['contact_info'] is not None:
            result['PersonMobilePhone'] = trainee_json['contact_info']['phone']
        if trainee_json['address_info'] is not None:
            try:
                result['Address__c'] = str(trainee_json['address_info']['address_1']) + str(
                    trainee_json['address_info']['address_2'])
            except UnicodeEncodeError:
                pass
            # result['ZIP__c'] = trainee_json['address_info']['postcode']
            result['City__c'] = trainee_json['address_info']['city']
        result['OwnerId'] = owner_id
        result['RecordTypeId'] = '01220000000V4Gu'
        result['Opportunity__c'] = opportunity_id
        return result

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
        if expa_json['status'] is not None:
            result['EXPA_EP_Status__c'] = expa_json['status'].title()
        result['EXPA_SignUp_Date__c'] = expa_json['created_at']
        if expa_json['gender'] is not None:
            result['Gender__c'] = expa_json['gender'].title()
        result['Induction_or_Interview__c'] = expa_json['interviewed']
        if expa_json['profile'] is not None:
            person_json = expa_json['profile']
            result['EXPA_Programmes__c'] = ';'.join(EXPASalesforceConverter.get_programmes(person_json))
            if person_json['duration_min'] is not None:
                result['Minimum_Duration__c'] = person_json['duration_min']
                result['Minimum_Duration_of_Internship__c'] = person_json['duration_min']
            if person_json['duration_max'] is not None:
                result['Maximum_Duration__c'] = person_json['duration_max']
                result['Maximum_Duration_of_Internship__c'] = person_json['duration_max']
            result['Earliest_Start_Date__c'] = person_json['earliest_start_date']
            result['Latest_End_Date__c'] = person_json['latest_end_date']
            result['EXPA_Skills__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['skills'])
            result['EXPA_Languages__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['languages'])
            result['EXPA_Backgrounds__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['backgrounds'])
            result['EXPA_Issues__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['issues'])
            result['EXPA_Work_Fields__c'] = EXPASalesforceConverter.collect_from_picklist(person_json['work_fields'])
            result['EXPA_Preferred_Organisations__c'] = EXPASalesforceConverter.collect_from_picklist(
                person_json['preferred_organisations'])
            regions = []
            countries = []
            region_ids = {1632, 1626, 1628, 1629, 1630, 1631, 1627}
            for location in person_json['preferred_locations_info']:
                if location['id'] in region_ids:
                    name = location['name']
                    if location['id'] == 1626:
                        name = "Worldwide"
                    regions.append(name)
                else:
                    countries.append((location['name'].title()))
            region_string = ';'.join(regions)
            country_string = ';'.join(countries)
            result['Area_of_world_interested_in_going__c'] = region_string
            result['Regional_Preferences__c'] = region_string
            result['specific_countries__c'] = country_string
            result['Country_Preference__c'] = country_string
        return result

    def convert_opp_expa_json_to_salesforce_dictionary(self, expa_json):
        logging.debug('Opportunity JSON: %s: ', expa_json)
        name = expa_json['title']
        if len(name) > 80:
            name = name[:80]
        result = {'Name': name}
        logging.info('Loading %s from EXPA...', result['Name'])
        result['Number_of_openings__c'] = expa_json['openings']
        for programme in expa_json['programmes']:
            if programme['id'] == 2:
                result['Internship_Type__c'] = 'Global Internship Programme'
            else:
                result['Internship_Type__c'] = 'Global Community Development Programme'
        if expa_json['specifics_info'] is not None:
            salary = expa_json['specifics_info']['salary']
            if salary is not None:
                if len(salary) > 31:
                    salary = salary[:31]
                    result['EXPA_Salary__c'] = salary
        if expa_json['host_lc'] is not None:
            office_id = expa_json['host_lc']['id']
        else:
            office_id = expa_json['home_lc']['id']
        try:
            result['OwnerId'] = self.lc_owner_mapper.op_to_sf(office_id)
            result['LC__c'] = self.lc_sfname_mapper.op_to_city(office_id)
        except KeyError:
            logging.error("The EP has an invalid current office: {0}".format(office_id))
        result['Form_Status__c'] = expa_json['current_status'].title()
        result['Opportunity_ID__c'] = expa_json['id']
        result['EXPA_url__c'] = 'https://experience.aiesec.org/#/opportunities/{0}'.format(expa_json['id'])
        result['Created_Date__c'] = expa_json['created_at']
        result['Application_Deadline__c'] = expa_json['applications_close_date']
        result['of_Applicants__c'] = expa_json['applications_count']
        result['Start__c'] = expa_json['earliest_start_date']
        result['Enddate__c'] = expa_json['latest_end_date']
        result['Minimum_Duration_Weeks__c'] = expa_json['duration_min']
        result['Maximum_Duration_Weeks__c'] = expa_json['duration_max']
        result['field_of_work__c'] = EXPASalesforceConverter.collect_from_multipicklist(expa_json['work_fields'])
        result['Background__c'] = EXPASalesforceConverter.collect_from_multipicklist(expa_json['backgrounds'])
        result['Languages_preferred__c'] = EXPASalesforceConverter.collect_languages(expa_json['languages'], False)
        result['Languages__c'] = EXPASalesforceConverter.collect_languages(expa_json['languages'])
        result['Level_of_Study__c'] = EXPASalesforceConverter.collect_from_multipicklist(expa_json['study_levels'])
        return result
