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

# --- Constants & Configuration ---
# (Your existing constants remain here, no changes needed)
MEMBERSHIP_TYPES = { -1: "All", 254: "BungieNext", 1: "Xbox", 2: "Playstation", 3: "Steam", 6: "Epic Games"}
BASE_BUNGIE_URL = "https://www.bungie.net"
BASE_API_URL = f"{BASE_BUNGIE_URL}/Platform"
BASE_AUTH_URL = f"{BASE_BUNGIE_URL}/en/oauth/authorize"
REDIRECT_URL = os.getenv("REDIRECT_URL", "https://127.0.0.1:5000/callback")
TOKEN_URL = f"{BASE_API_URL}/app/oauth/token/"
GET_USER_DETAILS_ENDPOINT = f"{BASE_API_URL}/User/GetCurrentBungieNetUser/"
GET_DESTINY_PROFILE_ENDPOINT_TEMPLATE = f"{BASE_API_URL}/Destiny2/{{}}/Profile/{{}}/"
GET_MANIFEST_ENDPOINT = f"{BASE_API_URL}/Destiny2/Manifest/"
MANIFEST_DB_PATH = None
LAST_MANIFEST_CHECK = 0
MANIFEST_CACHE_DURATION = 3600

# --- Helper Functions ---
def load_credentials():
    api_key = os.getenv("API_KEY")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    return api_key, client_id, client_secret

def get_api_data(current_session, url, headers, params=None):
    try:
        response = current_session.get(url=url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"ERROR during API call to {url}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"API Error Details: {e.response.text}")
        return None

def select_destiny_profile(parsed_linked_profiles_val):
    if not parsed_linked_profiles_val or 'Response' not in parsed_linked_profiles_val: return None
    destiny_profiles = parsed_linked_profiles_val.get('Response', {}).get('profiles', [])
    if not destiny_profiles: return None
    selected_profile = next((p for p in destiny_profiles if p.get('isCrossSavePrimary')), destiny_profiles[0])
    return selected_profile

def get_character_info(session, headers, destiny_profile):
    membership_type =  destiny_profile.get('membershipType')
    membership_id = destiny_profile.get('membershipId')
    if not all([membership_type, membership_id]): return None
    destiny_profile_url = GET_DESTINY_PROFILE_ENDPOINT_TEMPLATE.format(membership_type, membership_id)
    profile_components = {'components': '200'}
    profile_data = get_api_data(session, destiny_profile_url, headers, params=profile_components)
    if not profile_data or "Response" not in profile_data or "characters" not in profile_data["Response"]: return None
    return profile_data.get("Response", {}).get("characters", {}).get("data")

def get_manifest_location(headers):
    try:
        response = requests.get(GET_MANIFEST_ENDPOINT, headers=headers)
        response.raise_for_status()
        return BASE_BUNGIE_URL + response.json()['Response']['mobileWorldContentPaths']['en']
    except Exception as e: return None

def download_manifest(manifest_url):
    global MANIFEST_DB_PATH
    try:
        response = requests.get(manifest_url)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as manifest_zip:
            db_filename = manifest_zip.namelist()[0]
            manifest_zip.extract(db_filename)
            MANIFEST_DB_PATH = db_filename
            return db_filename
    except Exception as e: return None

def query_manifest(table_name, hash_id):
    if not MANIFEST_DB_PATH: return None
    try:
        con = sqlite3.connect(MANIFEST_DB_PATH)
        cur = con.cursor()
        if hash_id > 2147483647: hash_id -= 4294967296
        query_str = f"SELECT json FROM {table_name} WHERE id = ?"
        cur.execute(query_str, (hash_id,))
        result = cur.fetchone()
        con.close()
        if result: return json.loads(result[0])
    except Exception as e: return None

def update_manifest_if_needed():
    global LAST_MANIFEST_CHECK, MANIFEST_DB_PATH
    current_time = time.time()
    if current_time - LAST_MANIFEST_CHECK > MANIFEST_CACHE_DURATION:
        headers = {'X-API-KEY': os.getenv("API_KEY")}
        manifest_url = get_manifest_location(headers)
        if manifest_url:
            download_manifest(manifest_url)
            LAST_MANIFEST_CHECK = current_time

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

# --- Flask Routes ---
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/login')
def login():
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val: return "Error: Missing Credentials"
    current_session = OAuth2Session(client_id=client_id_val, redirect_uri=REDIRECT_URL)
    auth_link_tuple = current_session.authorization_url(BASE_AUTH_URL)
    session['oauth_state'] = auth_link_tuple[1]
    return redirect(auth_link_tuple[0])

@app.route('/callback')
def callback():
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val: return "Error: Missing Credentials"
    if request.args.get('state') != session.get('oauth_state'): return "Error: State mismatch."
    current_session = OAuth2Session(client_id=client_id_val, redirect_uri=REDIRECT_URL)
    try:
        token = current_session.fetch_token(TOKEN_URL, client_secret=client_secret_val, authorization_response=request.url)
        session['oauth_token'] = token
    except Exception as e:
        return f"Error: Failed to fetch token: {e}"
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    """ The main dashboard route where data is fetched and displayed. """
    api_key_val, client_id_val, client_secret_val = load_credentials()
    if not api_key_val: return "Error: Missing credentials"
    
    token = session.get('oauth_token')
    if not token: return redirect('/')
    
    additional_headers_val = {'X-API-KEY': api_key_val}
    authenticated_session = OAuth2Session(client_id=client_id_val, token=token)

    update_manifest_if_needed()

    svg_sprite_content = ""
    try:
        sprite_path = os.path.join(app.static_folder, 'Conflux-Icons.svg')
        with open(sprite_path, 'r', encoding='utf-8') as f:
            svg_sprite_content = f.read()
    except Exception as e:
        print(f"Warning: Could not read SVG sprite file. Icons may not display. Error: {e}")

    user_details = get_api_data(authenticated_session, GET_USER_DETAILS_ENDPOINT, additional_headers_val)
    if not user_details: return "Error fetching user details."

    bnet_membership_id = user_details.get('Response', {}).get('membershipId')
    linked_profiles_url = f"{BASE_API_URL}/Destiny2/254/Profile/{bnet_membership_id}/LinkedProfiles/"
    linked_profiles = get_api_data(authenticated_session, linked_profiles_url, additional_headers_val)
    
    selected_profile = select_destiny_profile(linked_profiles)
    if not selected_profile: return "Could not determine Destiny profile."

    user_platforms = []
    applicable_types = selected_profile.get('applicableMembershipTypes', [])
    for m_type in applicable_types:
        platform_name = MEMBERSHIP_TYPES.get(m_type)
        if platform_name:
            user_platforms.append({
                "Name": platform_name,
                "IconPath": f"/static/Media/{platform_name.lower()}.png"
            })
            
    character_data_dict = get_character_info(authenticated_session, additional_headers_val, selected_profile)
    
    simple_char_data = []
    if character_data_dict:
        for char_id, char_info in character_data_dict.items():
            class_def = query_manifest('DestinyClassDefinition', char_info.get('classHash'))
            race_def = query_manifest('DestinyRaceDefinition', char_info.get('raceHash'))
            title_def = query_manifest('DestinyRecordDefinition', char_info.get('titleRecordHash'))
            
            simple_char_data.append({
                'id': char_id,
                'Race': race_def['displayProperties']['name'] if race_def else "Unknown Race",
                'Class': class_def['displayProperties']['name'] if class_def else "Unknown Class",
                'Light': char_info.get('light'),
                'Title': title_def['titleInfo']['titlesByGender']['Male'] if title_def and 'titleInfo' in title_def else "",
                'EmblemPath': BASE_BUNGIE_URL + char_info.get('emblemPath', ''),
                'EmblemBackgroundPath': BASE_BUNGIE_URL + char_info.get('emblemBackgroundPath', '')
            })

    # Pass the SVG sprite content to the template
    return render_template('dashboard.html', 
                           user_details=user_details, 
                           platforms=user_platforms,
                           char_data=simple_char_data,
                           svg_sprite_content=svg_sprite_content)

if __name__ == '__main__':
    app.run(port=5000, debug=True, ssl_context=("localhost+2.pem", "localhost+2-key.pem"))
