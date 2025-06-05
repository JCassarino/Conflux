# Importing necessary libraries
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import webbrowser
import os
load_dotenv()

# Constants for niceer looking output
BORDER = "-------------------------------------------------------"

api_key = os.getenv("API_KEY")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

base_auth_url = "https://www.bungie.net/en/oauth/authorize"
redirect_url = "https://github.com/JCassarino/Destiny-2-Loadout-Analyzer"
token_url = "https://www.bungie.net/platform/app/oauth/token/"

# The API endpoint to retrieve user details after authorization has been completed.
get_user_details_endpoint = "https://www.bungie.net/Platform/User/GetCurrentBungieNetUser/"

# Creating a new OAuth2 session object.
# In the parameters, we provide the client ID and the redirect URL.
session = OAuth2Session(client_id = client_id, redirect_uri = redirect_url)

# Uses a helper method to generate the authorization URL. This is where the user will be sent to log in and authorize the app.
# This method returns a tuple, where the first element is the URL, and the second element is a state token.
auth_link = session.authorization_url(base_auth_url)

# Using webbrowser to open the generated auth URL
webbrowser.open(auth_link[0])

# The user will open the link in their browser, log in to their Bungie.net account, and authorize the application.
# After authorization, they will be redirected to the redirect URL. 
# They need to copy the full URL from their browser's address bar and paste it back into the program.

print(f"{BORDER}")
print("Welcome to the Destiny 2 Loadout Analyzer!")
print("Please log in to your Bungie.net account to authorize the application.")
print(f"{BORDER}")
print("After logging in, you will be redirected to the redirect URL.")
print("Copy the full URL from your browser's address bar and paste it below.")
print(f"{BORDER}")
redirect_response = input("")

# Extracts the authorization code from the redirect response URL.
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