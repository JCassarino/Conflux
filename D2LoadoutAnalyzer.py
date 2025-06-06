# Importing necessary libraries
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import json
import webbrowser
import os
load_dotenv()

# Constants for nicer looking output
BORDER = "\n-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~\n"

api_key = os.getenv("API_KEY")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# Header for API calls
additional_headers = {'X-API-KEY': os.getenv('API_KEY')}

base_auth_url = "https://www.bungie.net/en/oauth/authorize"
redirect_url = "https://github.com/JCassarino/Destiny-2-Loadout-Analyzer"
token_url = "https://www.bungie.net/platform/app/oauth/token/"

# API endpoints:
get_user_details_endpoint = "https://www.bungie.net/Platform/User/GetCurrentBungieNetUser/"

# Creating a new OAuth2 session object.
# In the parameters, we provide the client ID and the redirect URL.
session = OAuth2Session(client_id = client_id, redirect_uri = redirect_url)

# Uses a helper method to generate the authorization URL. This is where the user will be sent to log in and authorize the app.
auth_link = session.authorization_url(base_auth_url)
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
print(f"{BORDER}")

# Extracts the authorization code from the redirect response URL.
session.fetch_token(
    client_id = client_id,
    client_secret = client_secret,
    token_url = token_url,
    authorization_response = redirect_response
    )

# Using an HTTP GET request to the Bungie API endpoint to retrieve user details. Calling get_current_bungie_net_user.
raw_user_details = session.get(url = get_user_details_endpoint, headers = additional_headers)

if raw_user_details.status_code != 200: 
    print("Failed to retrieve user details. Please check your API key and client credentials.")
    quit()


# If the request is successful, the response will contain user details in JSON format.
parsed_user_details = raw_user_details.json()

# Full API response for user details; Commented out, can be uncommented for debugging purposes.
"""
print("Formatted user details response from Bungie API:")
print(json.dumps(parsed_user_details, indent=4))
print(f"{BORDER}")
"""

# After successfully retrieving the user details, we can now proceed to get the user's profile info.
membership_id = parsed_user_details['Response']['membershipId']
membership_type = 254

get_linked_profiles = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/LinkedProfiles/"

raw_user_profiles = session.get(url = get_linked_profiles, headers = additional_headers)
parsed_user_profiles = raw_user_profiles.json()

for profile in parsed_user_profiles['Response']['profiles']:
    if profile['isCrossSavePrimary'] is True:
        membership_id = profile['membershipId']
        membership_type = profile['membershipType']

# Full API response for user profiles; Commented out, can be uncommented for debugging purposes.
"""
print("Formatted user profile response from Bungie API:")
print(json.dumps(parsed_user_profiles['Response']['profiles'], indent=4))
"""

print(f"Membership ID: {membership_id}")
print(f"Membership Type: {membership_type}")

print(f"{BORDER}")
print(f"Welcome, {parsed_user_details['Response']['displayName']}!")
print("Please select a character to analyze:")