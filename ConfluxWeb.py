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
import time

# Load environment variables
load_dotenv()

# Membership types for Destiny 2 profiles
MEMBERSHIP_TYPES = { -1: "All", 254: "BungieNext", 1: "Xbox", 2: "Playstation", 3: "Steam", 6: "Epic Games"}

# API URLs and Endpoints
BASE_BUNGIE_URL = "https://www.bungie.net"
BASE_API_URL = f"{BASE_BUNGIE_URL}/Platform"
BASE_AUTH_URL = f"{BASE_BUNGIE_URL}/en/oauth/authorize"
REDIRECT_URL = os.getenv("REDIRECT_URL", "https://127.0.0.1:5000/callback") # https://destiny-2-loadout-analyzer.onrender.com/callback 
TOKEN_URL = f"{BASE_API_URL}/app/oauth/token/"
GET_USER_DETAILS_ENDPOINT = f"{BASE_API_URL}/User/GetCurrentBungieNetUser/"
GET_DESTINY_PROFILE_ENDPOINT_TEMPLATE = f"{BASE_API_URL}/Destiny2/{{}}/Profile/{{}}/" # Templated: use .format(membership_type, membership_id)
GET_MANIFEST_ENDPOINT = f"{BASE_API_URL}/Destiny2/Manifest/"


# Manifest related variables 
MANIFEST_DB_PATH = None  # This will be set after downloading the manifest
LAST_MANIFEST_CHECK = 0  # Timestamp of the last manifest check
MANIFEST_CACHE_DURATION = 3600 # How often to check for a new manifest (in seconds)


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

    return selected_profile


def get_character_info(session, headers, destiny_profile):
    """
    Fetches character data for a given Destiny profile.
    Returns character data or None if it fails.
    """

    membership_type =  destiny_profile.get('membershipType')
    membership_id = destiny_profile.get('membershipId')

    if not all([membership_type, membership_id]):
        return None

    # Build the Destiny profile endpoint URL using the provided membership type and ID
    destiny_profile_url = GET_DESTINY_PROFILE_ENDPOINT_TEMPLATE.format(membership_type, membership_id)
    profile_components = {'components': '200'}

    # Call the API to get the Destiny profile data. Component 200 returns basic character info for all characters on a profile.
    profile_data = get_api_data(session, destiny_profile_url, headers, params=profile_components)

    if not profile_data or "Response" not in profile_data or "characters" not in profile_data["Response"]:
        return None
    
    return profile_data.get("Response", {}).get("characters", {}).get("data")


def get_manifest_location(headers):
    """
    Fetches the location of the latest manifest file from Bungie API
    """

    # Tries to fetch the manifest URL from the Bungie API. If fails, an HTTP Error is raised. If successful, it returns the manifest URL.
    try:
        manifest_response = requests.get(GET_MANIFEST_ENDPOINT, headers=headers)
        manifest_response.raise_for_status() 
        manifest_url = BASE_BUNGIE_URL + manifest_response.json()['Response']['mobileWorldContentPaths']['en']

    except Exception as e: 
        print(f"{ERROR}Failed to fetch manifest loation: {e}")
        return None

    return manifest_url


def download_manifest(manifest_url):
    """
    Downloads the Destiny 2 manifest file from the provided URL. Extracts the contents and saves them to a local SQLite database.
    Returns the path to the SQLite database file or None if it fails.
    """

    try:
        # Downloading the manifest file.
        response = requests.get(manifest_url)

        # Extracting the contents of the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as manifest_zip:
            files = manifest_zip.namelist()
            manifest_zip.extract(files[0])

        return files[0]



    except Exception as e:
        print(f"Failed to download or extract manifest: {e}")
        return None


def query_manifest(table_name, hash_id):
    """
    Given a table name and hash ID, queries the local SQLite database for the corresponding data.
    """

    try:

        # .connect is opening the SQLite database file. Also creates a cursor object to execute SQL queries.
        con = sqlite3.connect(MANIFEST_DB_PATH)
        cur = con.cursor()

        # Converting hash_id
        if hash_id > 2147483647:
            hash_id = hash_id - 4294967296

        # Template SQL query string to fetch the JSON data for the passed hash ID from the passed table.
        query_str = f"SELECT json FROM {table_name} WHERE id = ?"

        cur.execute(query_str, (hash_id,))

        result = cur.fetchone()

        con.close()

        if result:
            return json.loads(result[0])

    except Exception as e:
        print(f"Error querying manifest database: {e}")
        return None


def update_manifest_if_needed():
    """
    Checks if the manifest needs to be updated based on the last check time and the cache duration.
    If needed, it downloads the latest manifest and updates the local database path.
    """
    global LAST_MANIFEST_CHECK, MANIFEST_DB_PATH
    current_time = time.time()
    # If the last check was more than MANIFEST_CACHE_DURATION seconds ago, update the manifest
    if current_time - LAST_MANIFEST_CHECK > MANIFEST_CACHE_DURATION:
        headers = {'X-API-KEY': os.getenv("API_KEY")}
        manifest_url = get_manifest_location(headers)
        if manifest_url:
            MANIFEST_DB_PATH = download_manifest(manifest_url)
            LAST_MANIFEST_CHECK = current_time
            print(f"Manifest updated: {MANIFEST_DB_PATH}")
        else:
            print("Failed to update manifest.")
    else:
        print("Manifest is up-to-date. No update needed.")

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

# Code that excecutes once when the app starts
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

    # Parsing linked profiles to select the cross-save primary & display all linked platform icons
    selected_profile = select_destiny_profile(linked_profiles)
    user_platforms = []
    for membership in selected_profile.get('applicableMembershipTypes'):

        platform_data = {}
        platform_name = MEMBERSHIP_TYPES.get(membership)
        if not platform_name:
            continue
        platform_icon_path = f"/static/Media/{platform_name.lower()}.png"
        platform_data["Name"] = platform_name
        platform_data["IconPath"] = platform_icon_path
        user_platforms.append(platform_data)

    # Fetching character information for the selected Destiny profile: Basics like character names, levels, and classes. Updates the manifest if needed.    
    update_manifest_if_needed()
    character_data_dict = get_character_info(authenticated_session, additional_headers_val, selected_profile)

    simple_char_data = []  # List to hold simplified character data for rendering
    for char_id, char_info in character_data_dict.items():

        current_char = {}
        class_hash = char_info.get('classHash')
        race_hash = char_info.get('raceHash')
        title_hash = char_info.get('titleRecordHash')
        light = char_info.get('light')
        emblem_path = BASE_BUNGIE_URL + char_info.get('emblemPath', '/common/destiny2_content/icons/placeholder.png')  # Default to placeholder if no emblem path
        emblem_background_path = BASE_BUNGIE_URL + char_info.get('emblemBackgroundPath', '/common/destiny2_content/icons/placeholder.png')  # Default to placeholder if no emblem path

        # Querying the manifest for Guardian class.
        class_dict = query_manifest('DestinyClassDefinition', class_hash)
        if class_dict:
            class_str = class_dict['displayProperties']['name']
        else: 
            class_str = "Unknown Class"

        # Querying the manifest for Guardian race.
        race_dict = query_manifest('DestinyRaceDefinition', race_hash)
        if race_dict:
            race_str = race_dict['displayProperties']['name']
        else: 
            race_str = "Unknown Race"

        # Querying the manifest for Guardian title.
        title_dict = query_manifest('DestinyRecordDefinition', title_hash)
        if title_dict:
            title_str = title_dict['displayProperties']['name']
        else: 
            title_str = ""

        current_char['Race'] = race_str
        current_char['Class'] = class_str
        current_char['Light'] = light
        current_char['Title'] = title_str
        current_char['EmblemPath'] = emblem_path
        current_char['EmblemBackgroundPath'] = emblem_background_path
        simple_char_data.append(current_char)


    # Render the profile template
    return render_template('dashboard.html', 
                           user_details=user_details, 
                           platforms = user_platforms,
                           char_data=simple_char_data,
                           )

if __name__ == '__main__':
    # Run the Flask app on port 5000
    app.run(port=5000, debug=True, ssl_context=("localhost+2.pem", "localhost+2-key.pem"))  # Set debug=True for development mode