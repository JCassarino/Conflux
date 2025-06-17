# Importing necessary libraries
from flask import Flask, render_template, request, redirect, session
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import json
import webbrowser
import os
import requests # For non-authenticated requests (like the manifest)
import sqlite3  # For interacting with the SQLite database (manifest)
import zipfile  # For handling the .zip file (manifest)
import io       

# Load environment variables
load_dotenv()

# Membership types for Destiny 2 profiles
MEMBERSHIP_TYPES = { -1: "All", 254: "BungieNext", 1: "Xbox", 2: "Playstation", 3: "Steam", 6: "Epic Games"}

# API URLs and Endpoints
BASE_BUNGIE_URL = "https://www.bungie.net"
BASE_API_URL = f"{BASE_BUNGIE_URL}/Platform"
BASE_AUTH_URL = f"{BASE_BUNGIE_URL}/en/oauth/authorize"
REDIRECT_URL = os.getenv("REDIRECT_URL", "https://destiny-2-loadout-analyzer.onrender.com/callback")
TOKEN_URL = f"{BASE_API_URL}/app/oauth/token/"
GET_USER_DETAILS_ENDPOINT = f"{BASE_API_URL}/User/GetCurrentBungieNetUser/"
GET_DESTINY_PROFILE_ENDPOINT_TEMPLATE = f"{BASE_API_URL}/Destiny2/{{}}/Profile/{{}}/" # Templated: use .format(membership_type, membership_id)
GET_MANIFEST_ENDPOINT = f"{BASE_API_URL}/Destiny2/Manifest/"

# Manifest; 
MANIFEST_DB_PATH = None  # This will be set after downloading the manifest


# --Helper Functions--

def load_credentials():
    """Loads API credentials from environment variables."""

    api_key = os.getenv("API_KEY")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    return api_key, client_id, client_secret


def get_api_data(current_session, url, headers, params=None):
    """
    Generalized function that performs a GET request on a Bungie API endpoint.
    Returns the parsed JSON response if successful; None if an error occurs.
    """

    # print(f"Calling API: {url} with params: {params if params else 'None'}") # Uncomment for debugging

    try:
        response = current_session.get(url=url, headers=headers, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        parsed_response = response.json()
        # print(f"API Call Successful. Status: {response.status_code}") # Uncomment for debugging
        return parsed_response
    except Exception as e:
        print(f"ERROR during API call to {url}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"API Error Details: {e.response.text}")
        return None


def select_destiny_profile(parsed_linked_profiles_val):
    """
    Selects the primary Destiny profile from the linked profiles response.
    Returns a dictionary with the selected profile's details or None.
    """

    if not parsed_linked_profiles_val or 'Response' not in parsed_linked_profiles_val:
        return None

    destiny_profiles = parsed_linked_profiles_val.get('Response', {}).get('profiles', [])
    if not destiny_profiles:
        print("No Destiny game profiles found linked to this Bungie.net account.")
        return None

    selected_profile = None

    # Selects the cross-save primary profile if it exists.
    for profile in destiny_profiles:
        if profile.get('isCrossSavePrimary') is True:
            selected_profile = profile
            break

    # If no primary is explicitly marked, select the first available profile.
    if not selected_profile:
        selected_profile = destiny_profiles[0]

    return {
        "membership_id": selected_profile.get('membershipId'),
        "membership_type": selected_profile.get('membershipType'),
        "display_name": selected_profile.get('displayName')
    }


# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")


@app.route('/')
def welcome():
    """
    Welcome Route -- What the user sees when they first open the site. Only displays a welcome message and a login button.
    """

    return render_template('welcome.html')


@app.route('/login')
def login():
    """
    Login Route -- The user is redirected here to log in with bungie.net.
    """

     # Load API credentials using load_credentials(); Exits if any credential is missing.
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val:
        return

    # Creating a new OAuth2 session using client ID and the redirect URL.
    current_session = OAuth2Session(client_id=client_id_val, redirect_uri=REDIRECT_URL)

    # Uses a helper method to generate the authorization URL. This is where the user will be sent to log in and authorize the app.
    auth_link_tuple = current_session.authorization_url(BASE_AUTH_URL)
    auth_url = auth_link_tuple[0]

    # Store the state in the session for later validation
    session['oauth_state'] = auth_link_tuple[1]

    return redirect(auth_url)


@app.route('/callback')
def callback():
    """
    Callback Route -- This is where the user is redirected after logging in with bungie.net -- Sends user to the home page.
    """

    # Load API credentials using load_credentials(); Exits if any credential is missing.
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val:
        return

    code = request.args.get('code')
    state = request.args.get('state')

    if state != session.get('oauth_state'):
        return "State mismatch."

    current_session = OAuth2Session(client_id=client_id_val, redirect_uri=REDIRECT_URL)
    try:
        token = current_session.fetch_token(
            TOKEN_URL,
            client_secret=client_secret_val,
            authorization_response=request.url
        )
    except Exception as e:
        return f"Failed to fetch token: {str(e)}"

    # Store the token in the session for later use
    session['oauth_token'] = token

    return redirect('/dashboard')


@app.route('/dashboard')
def dashboard():
    """
    The dashboard will serve as the user's home base within the app. It will display the user's profile information, characters, and other relevant data. All other functionalities will be accessible from this page.
    """

    # Load API credentials using load_credentials(); Exits if any credential is missing.
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val:
        return

    # Check if the user is authenticated; generates an OAuth2 session with the stored token.
    additional_headers_val = {'X-API-KEY': api_key_val}
    token = session.get('oauth_token')
    if not token:
        return "You must log in first."
    authenticated_session = OAuth2Session(client_id=client_id_val, token=token)

    # Fetch user details
    try:
        user_details_response = authenticated_session.get(GET_USER_DETAILS_ENDPOINT, headers=additional_headers_val)
        user_details = user_details_response.json()
    except Exception as e:
        return f"Failed to fetch user details: {str(e)}"

    # Fetching Destiny profile information
    bnet_membership_id = user_details.get('Response', {}).get('membershipId')
    linked_profiles_url = f"{BASE_API_URL}/Destiny2/254/Profile/{bnet_membership_id}/LinkedProfiles/" 
    linked_profiles = get_api_data(authenticated_session, linked_profiles_url, additional_headers_val)
    destiny_profile_list = linked_profiles.get('Response', {}).get('profiles', [])

    user_platforms = []
    for profile in destiny_profile_list:
        platform_data = {}
        membership_type = profile.get('membershipType')
        if not membership_type or membership_type not in MEMBERSHIP_TYPES:
            continue
        platform_name = MEMBERSHIP_TYPES[profile.get('membershipType')]
        platform_user_name = profile.get('displayName')
        platform_icon_path = f"/static/Media/{platform_name.lower()}.png"
        platform_data["Name"] = platform_name
        platform_data["UserName"] = platform_user_name
        platform_data["IconPath"] = platform_icon_path
        user_platforms.append(platform_data)


    # Render the profile template with user details
    return render_template('dashboard.html', 
                           user_details=user_details, 
                           platforms = user_platforms)

if __name__ == '__main__':
    # Run the Flask app on port 5000
    app.run(port=5000, debug=True, ssl_context=("localhost+2.pem", "localhost+2-key.pem"))  # Set debug=True for development mode