# Importing necessary libraries
from flask import Flask, render_template, request, redirect, session
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

# Membership types for Destiny 2 profiles
MEMBERSHIP_TYPES = { -1: "All", 254: "BungieNext", 1: "Xbox", 2: "Playstation", 3: "Steam", 6: "Epic Games"}

# API URLs and Endpoints
BASE_BUNGIE_URL = "https://www.bungie.net"
BASE_API_URL = f"{BASE_BUNGIE_URL}/Platform"
BASE_AUTH_URL = f"{BASE_BUNGIE_URL}/en/oauth/authorize"
REDIRECT_URL = os.getenv("REDIRECT_URL", "https://127.0.0.1:5000/callback")
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

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

# Welcome Route
@app.route('/')
def welcome():
    return render_template('index.html')  # Render the index.html template

# Login Route
@app.route('/login')
def login():
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


# Callback Route
@app.route('/callback')
def callback():
    # Load API credentials using load_credentials(); Exits if any credential is missing.
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val:
        return

    code = request.args.get('code')
    state = request.args.get('state')

    if state != session.get('oauth_state'):
        return ERROR + "State mismatch."

    current_session = OAuth2Session(client_id=client_id_val, redirect_uri=REDIRECT_URL)
    try:
        token = current_session.fetch_token(
            TOKEN_URL,
            client_secret=client_secret_val,
            authorization_response=request.url
        )
    except Exception as e:
        return ERROR + f"Failed to fetch token: {str(e)}"

    # Store the token in the session for later use
    session['oauth_token'] = token

    return redirect('/profile')


# Profile Route
@app.route('/profile')
def profile():
    # Load API credentials using load_credentials(); Exits if any credential is missing.
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val:
        return

    additional_headers_val = {'X-API-KEY': api_key_val}

    token = session.get('oauth_token')
    if not token:
        return ERROR + "You must log in first."

    authenticated_session = OAuth2Session(client_id=client_id_val, token=token)

    # Fetch user details
    try:
        user_details_response = authenticated_session.get(GET_USER_DETAILS_ENDPOINT, headers=additional_headers_val)
        user_details = user_details_response.json()
    except Exception as e:
        return ERROR + f"Failed to fetch user details: {str(e)}"

    # Render the profile template with user details
    return render_template('profile.html', user_details=user_details)

if __name__ == '__main__':
    # Run the Flask app on port 5000
    app.run(port=5000, debug=True, ssl_context=("localhost+2.pem", "localhost+2-key.pem"))  # Set debug=True for development mode