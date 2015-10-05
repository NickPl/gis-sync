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
    logging.basicConfig(filename='expa_sync.log'.format(str(datetime.datetime.today().date())), level=logging.DEBUG,
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
            persons = expa.get_people(date_to_sync)
            expa_salesforce_converter = EXPASalesforceConverter()
            for current_person in persons:
                salesforce_dictionary = expa_salesforce_converter.convert_expa_json_to_salesforce_dictionary(
                    current_person)
                email = salesforce_dictionary['Email']
                expa_id = salesforce_dictionary['EXPA_ID__c']
                full_name = salesforce_dictionary['FirstName'] + ' ' + salesforce_dictionary['LastName']
                if sf.does_account_exist(email) or sf.does_account_exist(email, expa_id):
                    logging.info('Updating account information for %s (%s)...', full_name, email)
                    sf.update_account(salesforce_dictionary)
                elif sf.does_lead_exist(email, expa_id):
                    logging.info('Updating lead information for %s (%s)...', full_name, email)
                    salesforce_dictionary.pop("OwnerId", None)
                    salesforce_dictionary.pop("Minimum_Duration__c", None)
                    salesforce_dictionary.pop("Maximum_Duration__c", None)
                    salesforce_dictionary.pop("EXPA_SignUp_Date__c", None)
                    salesforce_dictionary.pop("Regional_Preferences__c", None)
                    salesforce_dictionary.pop("Country_Preference__c", None)
                    sf.update_lead(salesforce_dictionary)
                else:
                    expa_signup_date = datetime.datetime.strptime(salesforce_dictionary['EXPA_SignUp_Date__c'],
                                                                  '%Y-%m-%dT%H:%M:%SZ').date()
                    gis_launch_date = datetime.datetime.strptime('2014-11-05', '%Y-%m-%d').date()
                    if expa_signup_date >= gis_launch_date:
                        logging.info('Creating a new lead for %s (%s)...', full_name, email)
                        salesforce_dictionary['RecordTypeId'] = '01220000000MHoeAAG'
                        salesforce_dictionary['LeadSource'] = 'Opportunities Portal'
                        salesforce_dictionary.pop("Minimum_Duration__c", None)
                        salesforce_dictionary.pop("Maximum_Duration__c", None)
                        salesforce_dictionary.pop("EXPA_SignUp_Date__c", None)
                        salesforce_dictionary.pop("Regional_Preferences__c", None)
                        salesforce_dictionary.pop("Country_Preference__c", None)
                        sf.create_lead(salesforce_dictionary)
                    else:
                        logging.info(
                            'Not creating a new lead for %s (%s) because the sign up date is before the GIS launch date...',
                            full_name, email)
            logging.info("Sync has finished successfully!")
        except Exception:
            logging.exception("An error has occured while generating an EXPA access token!")
    except Exception:
        logging.exception("An error has occured while connecting to Salesforce!")


if __name__ == "__main__":
    main()
