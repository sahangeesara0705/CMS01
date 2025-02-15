import requests
from requests_oauthlib import OAuth1

API_KEY = "bW5APinH15pigAstEOrhTfqi5"
API_SECRET_KEY = "2T1rt5DhF1kbmIEsMQAimY1W62RtQcE2rfichYIg2P4sY2qV6j"
CLIENT_ID = "VWd4eW9vX1dnRWd0UnByY0tLUTA6MTpjaQ"
CLIENT_SECRET = "NkTgR7D0RILVwotF07BoXxZWMSE32tHm0XWXp9faJZMZi-1mOY"
REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZATION_URL = "https://api.twitter.com/oauth/authorize"
USER_INFO_URL = "https://api.twitter.com/1.1/account/verify_credentials.json"
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"

oauth_store = {}

def get_authorization_url():
    oauth = OAuth1(API_KEY, API_SECRET_KEY)
    response = requests.post(REQUEST_TOKEN_URL, auth=oauth)

    if response.status_code == 200:
        credentials = dict(x.split("=") for x in response.text.split("&"))
        oauth_token = credentials["oauth_token"]
        oauth_store[oauth_token] = credentials["oauth_token_secret"]
        oauth_token_secret = credentials["oauth_token_secret"]
        return f"{AUTHORIZATION_URL}?oauth_token={oauth_token}"

def get_user_data(self, query_params):
    if "oauth_token" in query_params and "oauth_verifier" in query_params:
        oauth_token = query_params["oauth_token"][0]
        oauth_verifier = query_params["oauth_verifier"][0]

        if oauth_token not in oauth_store:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid token")
            return

        oauth_token_secret = oauth_store.pop(oauth_token)

        oauth = OAuth1(API_KEY, API_SECRET_KEY, oauth_token, oauth_token_secret)
        response = requests.post(ACCESS_TOKEN_URL, auth=oauth, data={"oauth_verifier": oauth_verifier})

        if response.status_code == 200:
            credentials = dict(x.split("=") for x in response.text.split("&"))
            access_token = credentials["oauth_token"]
            access_token_secret = credentials["oauth_token_secret"]
            user_id = credentials["user_id"]
            screen_name = credentials["screen_name"]

            oauth = OAuth1(API_KEY, API_SECRET_KEY, access_token, access_token_secret)
            user_response = requests.get(USER_INFO_URL, auth=oauth, params={"include_email": "true"})
            if user_response.status_code == 200:
                user_data = user_response.json()
                name = user_data.get("name", "Unknown")
                profile_image_url = user_data.get("profile_image_url_https", "N/A")
            else:
                name = "Unknown"
                profile_image_url = "N/A"

            return {
                "name": name,
                "profile_image_url": profile_image_url
            }

        else:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Error getting access token")
