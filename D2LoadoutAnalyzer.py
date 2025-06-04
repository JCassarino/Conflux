# Import necessary libraries

# Combines the requests (Used to make HTTP requests) and oauthlib (OAuth Logic) libraires.
# OAuth2session is a special type of session that knows how to manage OAuth tokens and sign requests
from requests_oauthlib import OAuth2Session

# Load environment variables from a .env file, keeping them out of the main code.
# Used for storing sensitive information like API keys and secrets.
from dotenv import load_dotenv

# Standard Python library; used to interact with the OS.
import os

# Reads .env file, makes variables defined within available in the main code.
load_dotenv()

# Retrieving environment variables:
api_key = os.getenv("API_KEY")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# URLs for OAuth2 / API processes:

# The user will be sent to this URL to login with Bungie.net and authorize the application.
base_auth_url = "https://www.bungie.net/en/oauth/authorize"

# After login & authorization, the user will be redirected to this URL. This would usually be the website of the application.
# Inside of the URL will be a authorization code, placed in the query parameters by Bungie.net. 
# This is like bungie sending you back to the app with a signed permission slip, granting the app access to your account.
redirect_url = "https://github.com/JCassarino/Destiny-2-Loadout-Analyzer"

# The program contacts this URL to exchange the authorization code for an access token.
token_url = "https://www.bungie.net/platform/app/oauth/token/"

# The API endpoint to retrieve user details after authorization has been completed.
get_user_details_endpoint = "https://www.bungie.net/Platform/User/GetCurrentBungieNetUser/"

# Creating a new OAuth2 session object.
# In the parameters, we provide the client ID and the redirect URL.
session = OAuth2Session(client_id = client_id, redirect_uri = redirect_url)

# Uses a helper method to generate the authorization URL. This is where the user will be sent to log in and authorize the app.
# This method returns a tuple, where the first element is the URL, and the second element is a state token.
auth_link = session.authorization_url(base_auth_url)
print(f"Auth Link: {auth_link[0]}")

# The user will open the link in their browser, log in to their Bungie.net account, and authorize the application.
# After authorization, they will be redirected to the redirect URL. 
# They need to copy the full URL from their browser's address bar and paste it back into the program.
redirect_response = input("Paste your redirect URL with query parameters here...")

# Extracts the authorization code from the redirect response URL.
# It then sends this code, along with the client ID and secret (proving that it's really your program), to the token URL.
# If all is correct, Bungie.net will respond with an access token, and a refresh token.
session.fetch_token(
    client_id = client_id,
    client_secret = client_secret,
    token_url = token_url,
    authorization_response = redirect_response
    )

# Bungie's API requires an API key with each request. This header identifies the application making the request.
additional_headers = {'X-API-KEY': os.getenv('API_KEY')}

# Using an HTTP GET request to the Bungie API endpoint to retrieve user details. Calling get_current_bungie_net_user.
response = session.get(url = get_user_details_endpoint, headers = additional_headers)

# Print the response status, reason, and text to see the result of the API call.
print(f"RESPONSE STATUS: {response.status_code}")
print(f"RESPONSE REASON: {response.reason}")
print(f"RESPONSE TEXT: \n{response.text}")