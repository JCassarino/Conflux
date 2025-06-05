# Destiny 2 Loadout Analyzer

## About The Project

Destiny 2 Loadout Analyzer is a tool designed to provide in-depth analysis of a Destiny 2 player's current build. By accessing character inventory and vault data via the Bungie.net API, this application aims to identify the equipped abilities, weapons, and armor to determine the build's archetype, evaluate its strengths and weaknesses, and offer potential improvements or alternative configurations.

The primary goal is to help players better understand their loadouts, optimize their builds for various activities, and discover new synergistic combinations.

## Core Functionality

The application will perform the following key functions:

1.  **Data Import:**
    * Connect to the Bungie.net API to fetch a player's character inventories (for all characters).
    * Retrieve the contents of the Guardian's vault.

2.  **Loadout Identification:**
    * **Abilities:** Parse equipped class, subclass, grenade, melee, class ability, Aspects, and Fragments.
    * **Weapons:** Identify all equipped weapons, including their class, frame, and perks.
    * **Armor:** Identify all equipped armor pieces, including their stats, mods, and exotic perks.

3.  **Build Analysis:**
    * **Archetype Classification:** Determine the type of build the player is currently running. This involves recognizing common combinations of abilities, exotics, and weapon types, as well as identifying prevalent keywords (scorch, devour, frost armor etc.).
    * **Synergy Evaluation:** Analyze how well the equipped items and abilities work together. For example, does the weapon match the subclass element, and do those match the siphon mods or surges on the armor?
    * **Strengths Identification:** Highlight the strong points of the current build.
    * **Weaknesses Identification:** Pinpoint potential shortcomings, such as low resilience, unused mod energy, or poor synergy between equipped items.

4.  **Improvement Suggestions:**
    * Offer recommendations for alternative gear (weapons, armor, exotics) that could enhance the current build or address identified weaknesses.
    * Suggest different mod configurations for armor.
    * Propose alternative Aspects or Fragments that might better suit the build's focus or improve its overall effectiveness.

## How It Will Work (Conceptual Overview)

1.  **Authentication:** User authenticates with Bungie.net to grant the application permission to read their Destiny 2 character data.
2.  **Data Fetching:** The application makes requests to the Bungie.net API to retrieve inventory, character, and vault information. This includes item instance IDs, definition hashes, and character progression.
3.  **Manifest Interaction:** Item definition hashes are used to look up detailed information from the Destiny 2 Manifest (e.g., item names, perk descriptions, stat values, ability effects).
4.  **Data Processing & Logic:** The core logic of the application processes the collected data, applying rules and heuristics to identify build components and synergies.
5.  **Analysis & Reporting:** The results of the analysis, including the build type, strengths, weaknesses, and suggestions, are presented to the user.

## Technologies

* **Primary Language:** Python
* **API Interaction:** Bungie.net API
* **Libraries:**
    * `requests` (for HTTP calls)
* **User Interface (TBD):** Could range from a command-line interface (CLI) to a web application.
 
## Links & Useful Info
* **[Bungie API Intro](https://www.bungie.net/en/Forums/Post/85087279?sort=0&page=0)**
* **[Bungie.net Applications Page](https://www.bungie.net/en/Application)**
* **[Bungie OAuth2 Documentation](https://github.com/Bungie-net/api/wiki/OAuth-Documentation)**
* **[Endpoints Wiki](https://destinydevs.github.io/BungieNetPlatform/docs/Endpoints)**
