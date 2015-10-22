import requests
import logging
import gis_token_generator


class EXPAWrapper:
    def __init__(self, email, password):
        self.token_generator = gis_token_generator.GISTokenGenerator(email, password)
        self.access_token = ''
        self.base_url = 'https://gis-api.aiesec.org:443/v1/'
        self.people_url = self.base_url + 'people/'
        self.opportunity_url = self.base_url + 'opportunities/'

    @staticmethod
    def format_date_time(date_time):
        return date_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    def fire_request(self, url):
        if self.access_token == '':
            self.access_token = self.token_generator.generate_token()
        while True:
            result = requests.get(url.format(self.access_token), verify=False)
            if result.status_code != 200:
                logging.error('Error: {0}'.format(result.json()))
            if result.status_code == 401:
                self.access_token = self.token_generator.generate_token()
            if result.status_code == 200:
                break
        return result.json()

    def get_page_number(self, last_interaction=None):
        url = self.base_url + 'people.json?access_token={0}&per_page=200'
        if last_interaction is not None:
            url += '&filters%5Blast_interaction%5D%5Bfrom%5D=' + EXPAWrapper.format_date_time(last_interaction)
        current_page = self.fire_request(url)
        return current_page['paging']['total_pages']

    def get_people(self, last_interaction=None, page=None):
        url = self.base_url + 'people.json?access_token={0}&per_page=200'
        if last_interaction is not None:
            url += '&filters%5Blast_interaction%5D%5Bfrom%5D=' + EXPAWrapper.format_date_time(last_interaction)
        current_page = self.fire_request(url)
        logging.debug('Current page from EXPA: {0}'.format(current_page))
        total_items = current_page['paging']['total_items']
        logging.info('Loading %d EPs from EXPA...', total_items)
        total_pages = current_page['paging']['total_pages']
        result = []
        if page is None:
            start_page = 1
            end_page = total_pages + 1
        else:
            start_page = page
            end_page = start_page + 1
        for c in range(start_page, end_page):
            current_page = self.fire_request(url + '&page=%d' % c)
            for i in current_page['data']:
                person = self.get_person_detail(i['id'])
                result.append(person)
        return result

    def get_person_detail(self, person_id):
        url = self.people_url + str(person_id) + '.json?access_token={0}'
        return self.fire_request(url)

    def get_opportunity_applicants(self, opportunity_id, existing_applicants, status=None, current_status=None):
        url = self.opportunity_url + str(opportunity_id) + '/applications.json?access_token={0}'
        if status is not None:
            url += '&filters%5Bstatus%5D=' + status
        current_page = self.fire_request(url)
        logging.debug('Current page from EXPA: {0}'.format(current_page))
        total_items = current_page['paging']['total_items']
        logging.info('Loading %d applicants from EXPA...', total_items)
        total_pages = current_page['paging']['total_pages']
        result = []
        start_page = 1
        end_page = total_pages + 1
        for c in range(start_page, end_page):
            current_page = self.fire_request(url + '&page=%d' % c)
            for i in current_page['data']:
                current_id = i['person']['id']
                if (current_status is None or i['person']['current_status'] == current_status) and current_id not in existing_applicants:
                    applicant = self.get_person_detail(current_id)
                    result.append(applicant)
        return result

    def get_match_data(self, opportunity_id, status_filter=None, person_id=None):
        opp_json = self.get_opportunity_detail(opportunity_id)
        if status_filter is None:
            status = opp_json['current_status']
        else:
            status = status_filter
        url = self.base_url + 'opportunities/' + str(opportunity_id) + '/applications.json?access_token={0}'
        url += '&filters%5Bstatus%5D=' + status
        app_json = self.fire_request(url)
        app_id = None
        print(app_json)
        for app in app_json['data']:
            if person_id is None or app['person']['id'] == person_id:
                app_id = app['id']
        if app_id is None:
            return None
        url = self.base_url + 'applications/' + str(app_id) + '.json?access_token={0}'
        app_data = self.fire_request(url)
        result = {"person": app_data['person']['id'], "matched_date": app_data['meta']['date_matched'], "realized_date": app_data['meta']['date_realized']}
        return result

    def get_opportunities(self, last_interaction=None, page=None):
        url = self.base_url + 'opportunities.json?access_token={0}&per_page=200'
        if last_interaction is not None:
            url += '&filters%5Blast_interaction%5D%5Bfrom%5D=' + EXPAWrapper.format_date_time(last_interaction)
        url += '&filters%5Bcountries%5B%5D=1596'
        url += '&filters%5Bprogrammes%5B%5D=1&filters%5Bprogrammes%5B%5D=2'
        current_page = self.fire_request(url)
        logging.debug('Current page from EXPA: {0}'.format(current_page))
        total_items = current_page['paging']['total_items']
        logging.info('Loading %d opportunities from EXPA...', total_items)
        total_pages = current_page['paging']['total_pages']
        result = []
        if page is None:
            start_page = 1
            end_page = total_pages + 1
        else:
            start_page = page
            end_page = start_page + 1
        for c in range(start_page, end_page):
            current_page = self.fire_request(url + '&page=%d' % c)
            for i in current_page['data']:
                opportunity = self.get_opportunity_detail(i['id'])
                result.append(opportunity)
        return result

    def get_opportunity_detail(self, opportunity_id):
        url = self.opportunity_url + str(opportunity_id) + '.json?access_token={0}'
        return self.fire_request(url)
