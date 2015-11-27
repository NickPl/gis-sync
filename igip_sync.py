import datetime
import salesforce_wrapper
import expa_wrapper
from credentials_store import credentials
import logging
import sys
from expa_salesforce_converter import EXPASalesforceConverter


class StreamToLogger(object):
    """
   Fake file-like stream object that redirects writes to a logger instance.
   """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


def main():
    logging.basicConfig(filename='expa_igip_sync.log'.format(str(datetime.datetime.today().date())),
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s')
    stdout_logger = logging.getLogger('')
    sl = StreamToLogger(stdout_logger, logging.INFO)
    sys.stdout = sl
    stderr_logger = logging.getLogger('')
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl
    logging.info("Connecting to Salesforce...")
    try:
        sf = salesforce_wrapper.SalesforceWrapper(
            credentials["salesforce"]["user"], credentials["salesforce"]["password"], credentials["salesforce"]["id"],
            credentials["salesforce"]["sandbox"])
        logging.info("Generating an EXPA access token...")
        try:
            expa = expa_wrapper.EXPAWrapper(credentials["expa"]["user"], credentials["expa"]["password"])
            if len(sys.argv) > 1 and sys.argv[1] == 'daily':
                date_to_sync = datetime.datetime.today() - datetime.timedelta(hours=26)
                logging.info("Starting daily sync...")
            else:
                date_to_sync = datetime.datetime.today() - datetime.timedelta(minutes=180)
                logging.info("Starting continuous sync...")
            opportunities = expa.get_opportunities(date_to_sync)
            expa_salesforce_converter = EXPASalesforceConverter()
            for current_opportunity in opportunities:
                salesforce_dictionary = expa_salesforce_converter.convert_opp_expa_json_to_salesforce_dictionary(
                    current_opportunity)
                expa_id = salesforce_dictionary['Opportunity_ID__c']
                expa_id_company = current_opportunity['branch']['company_id']
                name = salesforce_dictionary['Name']
                if sf.does_opportunity_exist(expa_id):
                    logging.info('Updating opportunity information for %s (%s)...', name, expa_id)
                    record_id = sf.update_opportunity(salesforce_dictionary, expa_id_company)
                    status_lower = salesforce_dictionary['Form_Status__c'].lower()
                    if status_lower in {'approved', 'matched', 'realized', 'completed'}:
                        logging.info('Found a matched TN--looking for applicants...')
                        applicants = expa.get_opportunity_applicants(expa_id, status_lower)
                        existing_applicants = sf.get_applicants(record_id)
                        logging.info('Found {0} EXPA applicants, {1} on Salesforce...'.format(len(applicants), len(existing_applicants)))
                        for applicant in applicants:
                            does_already_exist = False
                            for existing_applicant in existing_applicants:
                                logging.info("Comparing {0} and {1}...".format(applicant['id'], existing_applicant))
                                if applicant['id'] == existing_applicant:
                                    does_already_exist = True
                                    break
                            if not does_already_exist:
                                app_sf_dictionary = expa_salesforce_converter.convert_trainee_json_to_salesforce_dictionary(
                                    applicant, salesforce_dictionary['OwnerId'], record_id)
                                sf.create_account(app_sf_dictionary)
                            does_match_object_exist = sf.does_match_object_exist(record_id)
                            logging.info("Getting match data: Looking for applicant with SF id: {0}, EXPA ID: {1}, app ID: {2}...".format(record_id, expa_id, applicant['id']))
                            match_data = expa.get_match_data(expa_id, None, applicant['id'])
                            if does_match_object_exist:
                                sf.update_match_object(record_id, match_data)
                            else:
                                sf.create_match_object(record_id, match_data)
                else:
                    expa_signup_date = datetime.datetime.strptime(salesforce_dictionary['Created_Date__c'],
                                                                  '%Y-%m-%dT%H:%M:%SZ').date()
                    gis_launch_date = datetime.datetime.strptime('2014-11-05', '%Y-%m-%d').date()
                    if expa_signup_date >= gis_launch_date:
                        logging.info('Creating a new opportunity for %s (%s)...', name, expa_id)
                        sf.create_opportunity(salesforce_dictionary, expa_id_company)
                    else:
                        logging.info(
                            'Not creating a new opportunity for %s (%s) because the sign up date is before the GIS launch date...',
                            name, expa_id)
            logging.info("Sync has finished successfully!")
        except Exception:
            logging.exception("An error has occured while generating an EXPA access token!")
    except Exception:
        logging.exception("An error has occured while connecting to Salesforce!")


if __name__ == "__main__":
    main()
