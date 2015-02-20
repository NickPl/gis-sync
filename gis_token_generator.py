import urllib
import urllib2
import cookielib
import json


class GISTokenGenerator:
    def __init__(self, email, password):
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.email = email
        self.login_data = urllib.urlencode({'user[email]': email, 'user[password]': password})

    def generate_token(self):
        self.opener.open('https://auth.aiesec.org/users/sign_in', self.login_data)
        for cookie in self.cj:
            if cookie.name == 'aiesec_token':
                token_json = json.loads(urllib.unquote(cookie.value))
                token = token_json['token']['access_token']
        if token is None:
            raise Exception('Unable to generate a token for {0}!'.format(self.email))
        return token
