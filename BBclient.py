from requests_oauthlib import OAuth2Session
from os import environ
import sys


class AuthClient:

    client_id = None
    client_secret = None
    account_id = None
    redirect_uris = [
        'https://localhost'
    ]
    auth_uri = 'https://bitbucket.org/site/oauth2/authorize'
    token_uri = 'https://bitbucket.org/site/oauth2/access_token'
    server_base_uri = 'https://api.bitbucket.org/'
    BBClient = None
        

    def check_env(self):
        return environ.get('BB_ACCOUNT_ID') and environ.get('BB_OAUTH_ID') and environ.get('BB_OAUTH_SECRET')


    def setup_from_env(self):
        if not self.check_env():
            print("You must set all the environment variables for the OAUTH to work")
            sys.exit(1)

        self.account_id = environ.get('BB_ACCOUNT_ID')
        self.client_id = environ.get('BB_OAUTH_ID')
        self.client_secret = environ.get('BB_OAUTH_SECRET')


    def connect(self):

        # set secrets
        self.setup_from_env()

        # Fetch a request token
        self.BBClient = OAuth2Session(self.client_id)

        # Redirect user to Bitbucket for authorization
        authorization_url = self.BBClient.authorization_url(self.auth_uri)
        
        print('Please go here and authorize: {}'.format(authorization_url[0]))
        #self.openurl(authorization_url[0])

        # Get the authorization verifier code from the callback url
        redirect_response = input('Paste the full redirect URL here:')

        # Fetch the access token
        self.BBClient.fetch_token(
            self.token_uri,
            authorization_response=redirect_response,
            username=self.client_id,
            password=self.client_secret,
            client_secret=self.client_secret)

