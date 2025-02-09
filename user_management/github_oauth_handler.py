from http.client import responses

import requests
from urllib.parse import urlencode

CLIENT_ID = "Ov23liRXN4hsPQ7WwhKL"
CLIENT_SECRET = "36af13f05b52ba2251271e5a573e87255c2f7979"
REDIRECT_URI = "http://localhost:8000/callback"

# Redirect the user to GitHub's authorization page
def get_authorization_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "user",
        "state": "random_string_to_prevent_csrf"
    }
    auth_url = "https://github.com/login/oauth/authorize?" + urlencode(params)
    return auth_url

# Exchange the authorization code for an access token
def get_access_token(code):
    if not code:
        print("Code is missing. Cannot get access token")
        return
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Failed to get access token: {response.text}")

# Use the access token to fetch user data
def get_user_data(access_token):
    if not access_token:
        print("Access token is missing. Cannot fetch user data.")
        return
    url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch user data: {response.text}")

if __name__ == "__main__":
    auth_url = get_authorization_url()
    print(f"Visit the URL to authorize: {auth_url}")

    code = input("Enter the code from the callback URL: ")

    access_toekn = get_access_token(code)
    print(f"Access Token: {access_toekn}")

    user_data = get_user_data(access_toekn)
    print("User Data:", user_data)