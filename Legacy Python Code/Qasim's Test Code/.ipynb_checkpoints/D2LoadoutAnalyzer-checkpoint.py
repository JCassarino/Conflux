# Importing necessary libraries
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import json
import webbrowser
import os
import colorama
from colorama import Fore, Style, Back

# Load environment variables
load_dotenv()

# Initialize colorama to auto-reset colors after each print
colorama.init(autoreset=True)

# Constants for formatting
HEADER = Fore.MAGENTA + Style.BRIGHT
INFO = Fore.GREEN + Style.BRIGHT
ACTION = Fore.YELLOW
INPUT = Fore.BLUE
RESET = Style.RESET_ALL
BORDER = HEADER + "\n-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~\n"
CHECK = INFO + "✓"

# Membership types for Destiny 2 profiles
MEMBERSHIP_TYPES = { -1: "All", 254: "BungieNext", 1: "Xbox", 2: "Playstation", 3: "Steam", 6: "Epic Games"}

# API URLs and Endpoints
BASE_AUTH_URL = "https://www.bungie.net/en/oauth/authorize"
REDIRECT_URL = "https://github.com/JCassarino/Destiny-2-Loadout-Analyzer"
TOKEN_URL = "https://www.bungie.net/platform/app/oauth/token/"
GET_USER_DETAILS_ENDPOINT = "https://www.bungie.net/Platform/User/GetCurrentBungieNetUser/"
GET_LINKED_PROFILES_ENDPOINT_TEMPLATE = "https://www.bungie.net/Platform/Destiny2/{}/Profile/{}/LinkedProfiles/" # .format(membership_type, membership_id)
# GET_DESTINY_PROFILE_ENDPOINT_TEMPLATE = "https://www.bungie.net/Platform/Destiny2/{}/Profile/{}/" # .format(membership_type, membership_id)

def load_credentials():
    """Loads API credentials from environment variables."""

    api_key = os.getenv("API_KEY")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    return api_key, client_id, client_secret


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


def main():
    """Main function to orchestrate the application flow."""

    # Load API credentials using load_credentials(); Exits if any credential is missing.
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val:
        return

    # Header for API calls; Bungie requires an API key for all calls.
    additional_headers_val = {'X-API-KEY': api_key_val}

    # Gets an authenticated session using perform_oauth_flow(); Exits if it fails.
    authenticated_session = perform_oauth_flow(client_id_val, client_secret_val)
    if not authenticated_session:
        print("OAuth authorization failed. Exiting.")
        return

    # Retrieve bungie.net user details; Provides info necessary for subsequent API calls.
    print("Fetching Bungie.net user details...")
    parsed_user_details_val = get_api_data(authenticated_session, GET_USER_DETAILS_ENDPOINT, additional_headers_val)

    if not parsed_user_details_val or 'Response' not in parsed_user_details_val:
        print("User details not found. Exiting.")
        return

    # Full API response for user details; Commented out, can be uncommented for debugging.
    """
    print("Formatted user details response from Bungie API:")
    print(json.dumps(parsed_user_details_val, indent=4))
    print(BORDER)
    """

    # User details allow us to get the necessary profile info; Exits if it fails.
    bungie_net_user_response = parsed_user_details_val['Response']
    bnet_membership_id = bungie_net_user_response.get('membershipId')
    bnet_display_name = bungie_net_user_response.get('displayName', "Guardian")

    if not bnet_membership_id:
        print("Could not find Bungie.net membershipId. Exiting.")
        return

    print(f"\nFetching linked Destiny profiles for {INFO + bnet_display_name + RESET} (ID: {INFO + bnet_membership_id + RESET})...")
    # Membership type 254 is for BungieNext (the Bungie.net account itself) when getting linked profiles
    linked_profiles_url = GET_LINKED_PROFILES_ENDPOINT_TEMPLATE.format(254, bnet_membership_id)
    parsed_linked_profiles_val = get_api_data(authenticated_session, linked_profiles_url, additional_headers_val)

    if not parsed_linked_profiles_val or 'Response' not in parsed_linked_profiles_val or 'profiles' not in parsed_linked_profiles_val['Response']:
        print("Failed to retrieve linked profiles or the response was malformed. Exiting.")
        return

    destiny_profiles = parsed_linked_profiles_val['Response']['profiles']
    
    # Variables to store the selected Destiny platform profile details
    destiny_platform_membership_id = None
    destiny_platform_membership_type = None
    selected_profile_display_name = None

    if not destiny_profiles:
        print("No Destiny game profiles found linked to this Bungie.net account.")
    else:
        for profile in destiny_profiles:
            if profile.get('isCrossSavePrimary') is True:
                destiny_platform_membership_id = profile.get('membershipId')
                destiny_platform_membership_type = profile.get('membershipType')
                selected_profile_display_name = profile.get('displayName')
                break # Found the primary
        
        # Fallback if no primary is explicitly marked (e.g., pick the first one) # REVISE LATER TO ALLOW THE USER TO CHOOSEE
        if not destiny_platform_membership_id and destiny_profiles:
            print("No Cross Save primary profile found, selecting the first available Destiny profile.")
            profile = destiny_profiles[0]
            destiny_platform_membership_id = profile.get('membershipId')
            destiny_platform_membership_type = profile.get('membershipType')
            selected_profile_display_name = profile.get('displayName')

    # Full API response for user profiles; Commented out, can be uncommented for debugging purposes.
    """
    print("Formatted linked profiles response from Bungie API:")
    print(json.dumps(parsed_linked_profiles_val, indent=4)) # Print the whole linked profiles response
    """

    # If a Destiny profile was successfully selected, print the details; If not, print an error.
    if destiny_platform_membership_id and destiny_platform_membership_type is not None:
        print(BORDER)
        print(f"Selected Destiny Profile for API calls: {INFO + selected_profile_display_name}")
        print(f"Active Cross-Save Platform: {INFO + MEMBERSHIP_TYPES[destiny_platform_membership_type]}")
        print(BORDER)

        print(f"Welcome, {INFO + bnet_display_name}!")
        print("Please select a character to analyze:") # Placeholder for next steps

    else:
        print(BORDER)
        print(f"Welcome, {INFO + bnet_display_name}, we could not determine a Destiny profile to analyze.")
        print(BORDER)
        return

if __name__ == "__main__":
    main()
