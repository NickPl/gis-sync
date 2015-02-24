import datetime
import gis_token_generator
import salesforce_wrapper
import expa_wrapper
from credentials_store import credentials
import logging
import sys


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
    logging.basicConfig(filename='expa_initial_sync.log'.format(str(datetime.datetime.today().date())), level=logging.INFO,
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
            token_generator = gis_token_generator.GISTokenGenerator(credentials["expa"]["user"],
                                                                    credentials["expa"]["password"])
            access_token = token_generator.generate_token()
            expa = expa_wrapper.EXPAWrapper(access_token)
            total_pages = expa.get_page_number()
            for x in range(0, total_pages):
                persons = expa.get_all_records(None, x)
                for current_person in persons:
                    if sf.does_account_exist(current_person.email) or sf.does_ep_exist(current_person.email, current_person.id):
                        if sf.does_ep_exist(current_person.email, current_person.id):
                            logging.info('Updating EP information for %s (%s)...', current_person.full_name,
                                         current_person.email)
                            sf.update_ep(current_person.sf_dictionary)
                    elif sf.does_lead_exist(current_person.email, current_person.id):
                        logging.info('Updating lead information for %s (%s)...', current_person.full_name,
                                     current_person.email)
                        sf.update_lead(current_person.sf_dictionary)
                logging.info("Initial sync has finished successfully!")
        except Exception:
            logging.exception("An error has occured while generating an EXPA access token!")
    except Exception:
        logging.exception("An error has occured while connecting to Salesforce!")


if __name__ == "__main__":
    main()
