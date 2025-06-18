# Conflux

---

## About The Project

**Conflux** is envisioned as the ultimate **third-party home base** for every Destiny 2 player. Conflux aims to be a highly personalized dashboard that consolidates essential Guardian information, visualizes progress, and intelligently guides players through their Destiny 2 experience.

By leveraging the Bungie.net API, Conflux will provide a comprehensive overview of a chosen character's status, assess resources and gear, track quest and triumph progress, and offer tailored activity suggestions. Its primary goal is to empower players with clear, actionable insights, helping them optimize their playtime, refine their builds, and confidently pursue their next objectives.

---

## Current Functionality   --    **[Visit The Site!](https://destiny-2-loadout-analyzer.onrender.com)**

This application currently performs the following foundational operations, essential for future expansion:

1.  **Secure Authentication:**
    * Initiates a full **OAuth 2.0 authorization flow**, guiding the user to securely log in and authorize the application via the official Bungie.net website.
    * Successfully fetches and manages the necessary **access tokens** for making authenticated API calls.

2.  **Manifest Handling:**
    * Automatically fetches the location of the latest version of the **Destiny 2 Manifest** (the game's static database).
    * Downloads and extracts the Manifest database, making it available for local queries.
    * **Translates raw `hash` IDs** from the API into human-readable names (e.g., converting a `classHash` into "Titan", "Hunter", or "Warlock").

3.  **Profile and Character Retrieval:**
    * Fetches the user's main Bungie.net account details.
    * Retrieves all linked Destiny 2 game platform accounts (Xbox, PlayStation, Steam, etc.) and intelligently selects the **primary profile for analysis** (prioritizing the Cross-Save primary).
    * Fetches a list of all characters on the selected Destiny 2 profile.
    * Displays custom-formatted character cards, displaying each character's **class, race, and current Light Level** on a backdrop of their **currently equipped emblem**.

![Current Output]("static/Media/ConfluxDashboardHover.png")

---

## Intended Functionality

**Conflux** will evolve into a dynamic web application providing a central **homepage dashboard** for a chosen Guardian. This hub will offer a holistic view of your character and actionable recommendations:

### Character Overview & Status

1.  **Personalized Guardian Summary:**
    * A central dashboard displaying a quick overview of a selected character's key stats.
    * Summaries of critical **resources** (e.g., Glimmer, Enhancement Prisms, Ascendant Shards) and their current inventory counts.
    * Top-level status on seasonal rank, artifact power bonus, and active seasonal challenges.

2.  **Equipped Gear Showcase:**
    * A clear visual display of all currently **equipped weapons and armor**, including their names, icons, masterwork status, and perks.
    * Quick access to detailed information on each equipped item.

### Build Analysis & Management

3.  **In-Depth Build Analysis:**
    * **Component Identification:** Parse equipped abilities (class, subclass, grenade, melee, class ability, Aspects, Fragments), weapons (class, frame, perks), and armor (stats, mods, exotic perks).
    * **Synergy Evaluation:** Analyze how well all equipped items and abilities work together, including elemental matching, mod interactions, and exotic synergies.
    * **Strength & Weakness Assessment:** Highlight the strong points of the current build and pinpoint potential shortcomings (e.g., low resilience, unused mod energy, poor stat distribution).
    * **Keyword Detection:** Identify and explain how prevalent keywords (e.g., Scorch, Devour, Volatile, Blind, Suppress) are being generated and leveraged by the build.

4.  **Build Optimization & Suggestions:**
    * Offer **tailored recommendations** for alternative gear (weapons, armor, exotics) to enhance the current build or address identified weaknesses, potentially suggesting items from your vault.
    * Suggest different **mod configurations** for armor to optimize ability cooldowns, damage output, or survivability.
    * Propose alternative Aspects or Fragments that might better suit the build's focus or improve its overall effectiveness.
    * Identify **"God Rolls"** or highly sought-after weapon/armor perks based on community data or your own preferences.

### Activity & Progress Guidance

5.  **Intelligent Activity Suggestions:**
    * Based on your current **resources, gear level, active quests, uncompleted Triumphs, and seasonal challenges**, Conflux will suggest optimal activities.
    * Examples: "Complete Grandmaster Nightfall for Ascendant Shards," "Run today's Legend lost sector for Exotic Armor," "Complete bounties from Banshee-44 for enhancement prisms."
    * Highlight daily/weekly vendor bounties that align with your current goals.

6.  **Quest & Triumph Progress Tracking:**
    * Provide a clear summary of **active quests and their progress**.
    * Track progress towards **Triumphs and Seals**, highlighting nearest completions or most efficient paths.

7.  **Recent Activity Summary:**
    * Display a summary of your **most recent in-game activities** (e.g., Crucible matches, Strikes, Raids, Dungeons), including key statistics like K/D, completion time, and major rewards received.

8.  **Collection & Wishlist Integration:**
    * Track your progress towards completing in-game collections (weapons, armor, lore).
    * Allow users to build a "wishlist" of desired gear, and Conflux can then suggest activities or vendors that might drop those items.

---

## How It Will Work (Conceptual Overview)

1.  **Authentication:** User authenticates with Bungie.net to grant **Conflux** permission to read their Destiny 2 character data.
2.  **Data Fetching:** The application makes requests to the Bungie.net API to retrieve comprehensive inventory, character, vault, progression, and activity history information. This includes item instance IDs, definition hashes, and character progression.
3.  **Manifest Interaction:** Item definition hashes are used to look up detailed information from the Destiny 2 Manifest (e.g., item names, perk descriptions, stat values, ability effects).
4.  **Data Processing & Logic:** The core logic of the application processes the collected data, applying rules and heuristics to identify build components, synergies, assess progression, and generate activity suggestions.
5.  **Analysis & Reporting:** The results of the analysis, including the Guardian dashboard, build insights, suggested activities, and progress summaries, are presented to the user via an intuitive web interface.

---

## Technologies

* **Primary Language:** Python
* **API Interaction:** Bungie.net API
* **Libraries:**
    * `requests`
    * `webbrowser`
    * `dotenv`
    * `os`
    * `flask` (for the web version)
    * `requests_oauthlib`
    * `sqlite3`
    * `zipfile`
    * `io`
    * `colorama` (for CLI version)
* **User Interface:** Evolving from a command-line interface to a **full-fledged web application**.

---

## Links & Useful Info

* **[Bungie API Intro](https://www.bungie.net/en/Forums/Post/85087279?sort=0&page=0)**
* **[Bungie.net Applications Page](https://www.bungie.net/en/Application)**
* **[Bungie OAuth2 Documentation](https://github.com/Bungie-net/api/wiki/OAuth-Documentation)**
* **[Endpoints Wiki](https://destinydevs.github.io/BungieNetPlatform/docs/Endpoints)**
* **[Official Endpoint Documentation](https://bungie-net.github.io/multi/index.html)**
* **[Community Guide to Bungie API](https://paracausal.science/guide/)**
