import datetime
import gis_token_generator
import salesforce_wrapper
import expa_wrapper
from credentials_store import credentials
import logging


def perform_sync(last_interaction_date):
    logging.basicConfig(filename='{0}.log'.format(str(datetime.datetime.today().date())), level=logging.DEBUG,
                    format='%(asctime)s %(message)s')
    logging.info("Connecting to Salesforce...")
    try:
        sf = salesforce_wrapper.SalesforceWrapper(
            credentials["salesforce"]["user"], credentials["salesforce"]["password"], credentials["salesforce"]["id"],
            credentials["salesforce"]["sandbox"])
    except Exception:
        logging.error("An error has occured while connecting to Salesforce!")
    logging.info("Generating an EXPA access token...")
    try:
        token_generator = gis_token_generator.GISTokenGenerator(credentials["expa"]["user"],
                                                            credentials["expa"]["password"])
        access_token = token_generator.generate_token()
    except Exception:
        logging.error("An error has occured while generating an EXPA access token!")
    expa = expa_wrapper.EXPAWrapper(access_token)
    persons = expa.get_all_records(datetime.datetime.today().date())
    for current_person in persons:
        if sf.does_account_exist(current_person.email):
            if sf.does_ep_exist(current_person.email):
                logging.info('Updating EP information for %s (%s)...', current_person.full_name, current_person.email)
                sf.update_ep(current_person.sf_dictionary)
        elif sf.does_lead_exist(current_person.email):
            logging.info('Updating lead information for %s (%s)...', current_person.full_name, current_person.email)
            sf.update_lead(current_person.sf_dictionary)
        else:
            logging.info('Creating a new lead for %s (%s)...', current_person.full_name, current_person.email)
            sf.create_lead(current_person.sf_dictionary)


def perform_daily_sync():
    perform_sync(datetime.datetime.today() - datetime.timedelta(days=7))


def perform_continuous_sync():
    perform_sync(datetime.datetime.today() - datetime.timedelta(minutes=30))