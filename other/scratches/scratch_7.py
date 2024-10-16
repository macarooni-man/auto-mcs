import requests

# Retrieve worlds from CurseForge
def search_worlds(query: str):
    url = 'https://api.curse.tools/v1/cf/mods/search'
    params = {
        'gameId': 432,  # Minecraft game ID
        'classId': 17,  # Class ID for "Worlds"
        'pageSize': 50,
        'index': 0,
        'searchFilter': query
    }

    all_worlds = []

    # Loop over data until there is none left
    while True:
        response = constants.get_url(url, params=params, return_response=True)
        if response.status_code != 200:
            print(f"Error: {response.status_code} {response.text}")
            break
        try:
            data = response.json()
        except ValueError:
            print(f"Failed to parse JSON response: {response.text}")
            break
        mods = data.get('data', [])
        if not mods:
            break
        all_worlds.extend(mods)
        params['index'] += len(mods)

    return all_worlds

# print(search_worlds('parkour'))
from addons import *
import constants

check_cf()
constants.debug = True

properties = {"name": "Stock Vanilla", "type": "paper", "version": "1.21"}
addon_search = search_addons("worldedit", properties)
for a in addon_search:
    print(vars(a))

# # Update addon: pass in (jar_path, server_properties, new_version)
# jar_path = r"/Users/kaleb/Library/Application Support/auto-mcs/Servers/Stock Vanilla/plugins/WorldEdit.jar"
# try:
#     addon_file = get_addon_file(jar_path, properties)
#     addon_web = get_update_url(addon_file, '1.15')
#     success = download_addon(addon_web, properties, os.path.split(jar_path)[0])
#
#     # return (addon_web if addon_web else addon_file), success
#     print(vars(addon_web))
#
# except ConnectionRefusedError:
#     print("Cloudscraper failed")
