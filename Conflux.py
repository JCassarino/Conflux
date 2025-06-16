# Importing necessary libraries
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import json
import webbrowser
import os
import colorama
from colorama import Fore, Style, Back
import requests # For non-authenticated requests (like the manifest)
import sqlite3  # For interacting with the SQLite database
import zipfile  # For handling the .zip file
import io       

# Load environment variables
load_dotenv()

# Initialize colorama to auto-reset colors after each print
colorama.init(autoreset=True)

# --- Constants & Configuration ---

# Formatting
HEADER = Fore.MAGENTA + Style.BRIGHT
INFO = Fore.GREEN + Style.BRIGHT
ACTION = Fore.YELLOW
INPUT = Fore.BLUE
ERROR = Fore.RED + Style.BRIGHT
RESET = Style.RESET_ALL
BORDER = HEADER + "\n-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~\n"
CHECK = INFO + "✓"

# Membership types for Destiny 2 profiles
MEMBERSHIP_TYPES = { -1: "All", 254: "BungieNext", 1: "Xbox", 2: "Playstation", 3: "Steam", 6: "Epic Games"}

# API URLs and Endpoints
BASE_BUNGIE_URL = "https://www.bungie.net"
BASE_API_URL = f"{BASE_BUNGIE_URL}/Platform"
BASE_AUTH_URL = f"{BASE_BUNGIE_URL}/en/oauth/authorize"
REDIRECT_URL = "https://github.com/JCassarino/Destiny-2-Loadout-Analyzer"
TOKEN_URL = f"{BASE_API_URL}/app/oauth/token/"
GET_USER_DETAILS_ENDPOINT = f"{BASE_API_URL}/User/GetCurrentBungieNetUser/"
GET_DESTINY_PROFILE_ENDPOINT_TEMPLATE = f"{BASE_API_URL}/Destiny2/{{}}/Profile/{{}}/" # Templated: use .format(membership_type, membership_id)
GET_MANIFEST_ENDPOINT = f"{BASE_API_URL}/Destiny2/Manifest/"

# Manifest
MANIFEST_DB_PATH = None  # This will be set after downloading the manifest

def load_credentials():
    """Loads API credentials from environment variables."""

    api_key = os.getenv("API_KEY")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    return api_key, client_id, client_secret

#------------------------------------------------------------------------------- Above has been loaded into web version

def perform_oauth_flow(client_id_val, client_secret_val):
    """
    Handles the OAuth 2.0 authorization flow.
    Returns an authenticated OAuth2Session object or None if it fails.
    """

    # Creating a new OAuth2 session using client ID and the redirect URL.
    current_session = OAuth2Session(client_id=client_id_val, redirect_uri=REDIRECT_URL)

    # Uses a helper method to generate the authorization URL. This is where the user will be sent to log in and authorize the app.
    auth_link_tuple = current_session.authorization_url(BASE_AUTH_URL)
    auth_url = auth_link_tuple[0]
    
    # Using webbrowser to open the generated auth URL
    try:
        webbrowser.open(auth_url)
    except Exception as e:
        print(f"{BORDER}Could not open browser automatically: {e}")
        print(f"Please manually open this URL: {auth_url}{BORDER}")

    # After authorization, the user will be redirected to the redirect URL. 
    # They need to copy the full URL from their browser's address bar and paste it back into the program.
    print(BORDER)
    print("Welcome to the Destiny 2 Loadout Analyzer!")
    print(ACTION + "Please log in to your Bungie.net account in the browser window/tab that just opened.")
    print(BORDER)
    print("After authorizing, you will be redirected to a new page.")
    print(ACTION + "Copy the full URL from your browser's address bar.\n")
    redirect_response_url = input(INPUT + "Paste the full redirect URL here -> ")
    print(BORDER)

    # Extracts the authorization code from the redirect response URL.
    # If fetch_token fails, it will print an error message and return None.
    try:
        current_session.fetch_token(
            token_url=TOKEN_URL,
            client_id=client_id_val,
            client_secret=client_secret_val,
            authorization_response=redirect_response_url
        )
        return current_session

    except Exception as e:
        print(f"ERROR fetching token: {e}")
        print("Please ensure you pasted the correct full URL and that your client_id/client_secret are correct.")
        return None


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


def get_character_info(session, headers, destiny_profile):
    """
    Fetches character data for a given Destiny profile.
    Returns character data or None if it fails.
    """

    membership_type =  destiny_profile['membership_type']
    membership_id = destiny_profile['membership_id']

    if not all([membership_type, membership_id]):
        print(ERROR + "Missing membership type or ID.")
        return None

    # Build the Destiny profile endpoint URL using the provided membership type and ID
    destiny_profile_url = GET_DESTINY_PROFILE_ENDPOINT_TEMPLATE.format(membership_type, membership_id)
    profile_components = {'components': '200'}

    # Call the API to get the Destiny profile data. Component 200 returns basic character info for all characters on a profile.
    profile_data = get_api_data(session, destiny_profile_url, headers, params=profile_components)

    if not profile_data or "Response" not in profile_data or "characters" not in profile_data["Response"]:
        print(ERROR + "Failed to retrieve Destiny profile or character list.")
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
        print(f"{ERROR}Failed to download or extract manifest: {e}")
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
        print(f"{ERROR}Error querying manifest database: {e}")
        return None


def main():
    """Main function to orchestrate the application flow."""

    # Load API credentials using load_credentials(); Exits if any credential is missing.
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val:
        return

    # Header for API calls; Bungie requires an API key for all calls.
    additional_headers_val = {'X-API-KEY': api_key_val}

    # Downloads the manifest database if it doesn't exist.
    global MANIFEST_DB_PATH
    if not MANIFEST_DB_PATH:
        MANIFEST_DB_PATH = download_manifest(get_manifest_location(additional_headers_val))

    # Gets an authenticated session using perform_oauth_flow(); Exits if it fails.
    authenticated_session = perform_oauth_flow(client_id_val, client_secret_val)
    if not authenticated_session:
        print("OAuth authorization failed. Exiting.")
        return

    # Fetches the current Bungie.net user details using the authenticated session.
    #print("Fetching account information...")
    parsed_user_details_val = get_api_data(authenticated_session, GET_USER_DETAILS_ENDPOINT, additional_headers_val)
    if not parsed_user_details_val: return
    
    bnet_membership_id = parsed_user_details_val.get('Response', {}).get('membershipId')
    bnet_display_name = parsed_user_details_val.get('Response', {}).get('displayName', "Guardian")

    if not bnet_membership_id:
        print(f"{ERROR}Could not find Bungie.net membershipId. Exiting.")
        return

    # Using membershipType 254 (BungieNext) to get linked profiles.
    linked_profiles_url = f"{BASE_API_URL}/Destiny2/254/Profile/{bnet_membership_id}/LinkedProfiles/"
    parsed_linked_profiles_val = get_api_data(authenticated_session, linked_profiles_url, additional_headers_val)
    
    selected_destiny_profile = select_destiny_profile(parsed_linked_profiles_val)
    if not selected_destiny_profile:
        print(ERROR + "Could not determine a Destiny profile to analyze.")
        return

    character_data_dict = get_character_info(authenticated_session, additional_headers_val, selected_destiny_profile)
    
    if not character_data_dict:
        print("Could not retrieve character data.")
        return

    # Final output
    print(f"Welcome, {INFO + bnet_display_name}!")
    print(ACTION + "Please select a character below to analyze:")
    print(BORDER)
    
    for char_id, char_info in character_data_dict.items():

        class_hash = char_info.get('classHash')
        race_hash = char_info.get('raceHash')
        light = char_info.get('light')

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

        print(f"Character: {INFO}{race_str} {class_str}{RESET} | Light: {ACTION}{light}{RESET}")
    
    print(BORDER)

if __name__ == "__main__":
    main()