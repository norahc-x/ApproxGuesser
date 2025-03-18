# ApproxGuesser
This Discord bot uses Cloudflare’s cache hits to approximate a user’s region and draws circles on a static Google Map. It can randomize the bot’s avatar, send direct messages, and calculate an average location if multiple datacenters respond.

When the bot sends a direct message, its avatar URL may be cached by various Cloudflare datacenters. By checking each datacenter’s “cf-cache-status” header, the bot identifies which ones have stored (HIT) the avatar. This allows the bot to estimate a user’s approximate region by seeing where the content was cached and drawing circles on a map.

This code organizes the **datacenters list** in a separate file (`datacenters.py`) for cleaner readability.

## Features

- **Modular**: The large datacenters list is isolated in `datacenters_list.py`.
- **Random Bot Avatar**: The bot can randomly pick its avatar from `AVATAR_URLS`, or you can provide a custom URL for each command.
- **Datacenter HIT**: After sending a DM, the bot checks each datacenter to see which responded with "HIT".
- **Approximate Mapping**: The bot builds a URL to a Google Static Map, drawing:
  - **Orange circles** around the datacenters that responded with a HIT.
  - **Red and Blue circles** on the average location (if multiple datacenters are found). If only one datacenter is found, all three circles (orange, red, blue) are drawn on that single datacenter.
  - **Markers labeled "P" for each datacenter (and/or the average location, depending on how you customize it)..
- **Slash Commands**:
  - `/locate_id <user_id>`: DM user by numeric ID.
  - `/locate_name <username>`: DM user by name (cache-based).
  
## Setup

1. Create a Bot via the Discord Developer Portal.

    Copy the Bot Token.
    Enable the necessary Privileged Gateway Intents if needed (e.g., server members).

2. Google Maps API Key:

    Obtain a key from Google Cloud Console.
    Make sure “Static Maps” is enabled in your Google Maps API settings.

3. Set the following in the .py file:

    - TOKEN = "YOUR_BOT_TOKEN"
    - MY_USER_ID = 123456789012345678 (your numeric Discord user ID, if you want to restrict usage).
    - GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"

4. Clone the Repository

   ```bash
   https://github.com/norahc-x/ApproxGuesser.git

5. Install dependencies:
   ```bash
   pip install -r requirements.txt

## Usage

  - `/locate_id <user_id>`: `[avatar_url]`
  Sends a DM to a user by numeric ID. Tries to detect which datacenters responded with HIT, then shows a map.

  - `/locate_name <username>`: `[avatar_url]`
  Sends a DM to a user found in the bot’s user cache by name. Same triangulation logic as above.

After the DM is sent, the bot waits a few seconds for push notification caching, checks each datacenter, and displays any that respond with “HIT” in a static Google Map inside an embedded message.

## Demo

![demo1](https://github.com/user-attachments/assets/32322a1b-a80d-449e-9d6a-09dec69132b9)

Demo Scenario

  - The user executes `/locate_id <user_id>` (or `/locate_name <username>`) in a Discord channel.
  - The bot randomly selects (or sets) its avatar, then attempts up to 10 times to send a DM to your target until at least one Cloudflare datacenter responds with “HIT.”
  - After a brief pause (to allow push notifications), the bot checks which Cloudflare datacenter(s) responded with “HIT” for the bot’s avatar.
  - The bot returns an embedded map and a summary message indicating the datacenter city (or multiple datacenters) where the avatar was cached. If there’s only one datacenter, it draws three circles on that single location; if multiple, it draws orange circles on each datacenter and calculates an approximate midpoint, drawing additional red and blue circles at that average location.
  - Your target sees a direct message from the bot, and you see the resulting map and coordinates in the channel where you ran the command, showcasing the playful “triangulation” concept.


## Notes

 Notes

  - This is primarily an educational or demonstration project, illustrating how caching might give hints about a user’s region.
  - Accuracy is not guaranteed—this does not truly locate the user, and it is more a concept demonstration.
  - The code draws circles of a fixed radius (e.g., 300 km, 150 km, 75 km). You can tweak the radius in the `build_static_map` function.
  - For a real production scenario, always follow Discord’s Terms of Service and ensure you comply with privacy and data-gathering regulations.

## Contributing

Feel free to open issues or submit pull requests. This repository is open for improvements, additional features, or bug fixes.
