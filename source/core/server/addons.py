from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from zipfile import ZipFile
from copy import deepcopy
from shutil import copy
from glob import glob
import threading
import requests
import hashlib
import math
import json
import time
import os
import re

from source.core.constants import paths, is_semver
from source.core.server import manager
from source.core import constants


# Auto-MCS Add-on API
# --------------------------------------------- Global Functions -------------------------------------------------------

addon_cache = {}
addon_cache_version = 2
addon_cache_lock = threading.RLock()

# Grabs addon_cache if it exists
def load_addon_cache(write=False, telepath=False):

    if not telepath and constants.server_manager.current_server:
        telepath_data = constants.server_manager.current_server._telepath_data
        if telepath_data:
            return constants.api_manager.request(
                endpoint = '/addon/load_addon_cache',
                host = telepath_data['host'],
                port = telepath_data['port'],
                args = {'write': write, 'telepath': True}
            )

    global addon_cache
    file_path = os.path.join(paths.cache, "addon-db.json")

    # Loads data from dict
    if not write:
        try:
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    cache_data = json.load(file)

                with addon_cache_lock:
                    addon_cache = cache_data

        except:
            return

    else:
        try:
            constants.folder_check(paths.cache)

            with addon_cache_lock:
                temp_path = file_path + '.tmp'

                with open(temp_path, 'w', encoding='utf-8') as file:
                    json.dump(addon_cache, file, indent=2)

                os.replace(temp_path, file_path)

        except:
            return



# ----------------------------------------------- Addon Objects --------------------------------------------------------

# Log wrapper
def send_log(object_data, message, level=None):
    from source.core import logger
    return logger.send_log(f'{__name__}.{object_data}', message, level, 'core')

# Base AddonObject for others
class AddonObject():
    def _to_json(self):
        final_data = {k: getattr(self, k) for k in dir(self) if not (k.endswith('__') or callable(getattr(self, k)))}
        final_data['__reconstruct__'] = self.__class__.__name__
        return final_data

    # Returns a consistent identifier for comparison
    def _addon_key(self):
        class_name = self.__class__.__name__

        # Prefer the local file hash for imported add-ons
        if self.addon_object_type == 'file':
            addon_hash = str(getattr(self, 'hash', '') or '').strip().lower()
            if addon_hash:
                return (class_name, 'hash', addon_hash)

        addon_id = str(self.id or '').strip().lower()
        addon_type = str(self.type or '').strip().lower()
        addon_provider = str(getattr(self, 'provider', '') or '').strip().lower()

        # Prefer provider/project ID for downloadable add-ons
        if addon_id:
            return (class_name, addon_provider, 'id', addon_type, addon_id)

        # Fall back to descriptive identity
        return (
            class_name,
            addon_provider,
            'name',
            addon_type,
            str(self.name or '').strip().lower(),
            str(self.author or '').strip().lower()
        )

    def __eq__(self, other):
        if not isinstance(other, AddonObject):
            return False
        return self._addon_key() == other._addon_key()

    def __init__(self):
        self.addon_object_type = None
        self.name = None
        self.type = None
        self.author = None
        self.subtitle = None
        self.id = None
        self.url = None
        self.addon_version = None

# AddonObject for housing downloadable addons
class AddonWebObject(AddonObject):
    def __init__(self, addon_name, addon_type='', addon_author='', addon_subtitle='', addon_url='', addon_id='', addon_version=''):
        super().__init__()
        self.provider: str | None = None
        self.icon_url = None
        self.release_type = None

        if isinstance(addon_name, dict):
            [setattr(self, k, v) for k, v in addon_name.items()]

        else:
            self.addon_object_type = "web"
            self.name = addon_name
            self.type = addon_type
            self.author = addon_author
            self.subtitle = addon_subtitle
            self.url = addon_url
            self.id = addon_id
            self.addon_version = addon_version

            # To be updated in get_addon_info()
            self.supported = "unknown"
            self.versions = []
            self.description = None
            self.download_url = None
            self.download_version = None

    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__} '{self.name}' at '{self.url}'>"

# AddonObject for housing imported addons
class AddonFileObject(AddonObject):
    def __init__(self, addon_name, addon_type='', addon_author='', addon_subtitle='', addon_path='', addon_id='', addon_version=''):
        super().__init__()

        self.loaders = []

        self.update = {
            'version': None,
            'url': None,
            'is_updating': False,
        }

        if isinstance(addon_name, dict):
            [setattr(self, k, v) for k, v in addon_name.items()]

        else:
            self.addon_object_type = "file"
            self.name = addon_name
            self.type = addon_type
            self.author = addon_author
            self.subtitle = addon_subtitle
            self.id = addon_id
            self.path = addon_path
            self.addon_version = addon_version
            self.enabled = True

            # Generate Hash
            hash_data = int(hashlib.md5(f'{os.path.getsize(addon_path)}/{os.path.basename(addon_path)}'.encode()).hexdigest(), 16)
            self.hash = str(hash_data)[:8]

    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__} '{self.name}' at '{self.path}'>"

# AddonObject for housing downloadable modpacks
class ModpackWebObject(AddonWebObject):
    pass



# --------------------------------------------- Addon Providers -------------------------------------------------------

# Abstracts common provider behavior
class Provider():
    _cache = {}
    _cache_lock = threading.RLock()
    cache_ttl = 300

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

    # Generates a cache key for the current provider/target
    def _cache_key(self, method: str, *args):
        target = str(getattr(self, 'server_type', '') or '').lower()
        return (self.__class__, target, method, *args)

    # Returns an in-memory cached provider result
    def _get_cache(self, method: str, *args):
        key = self._cache_key(method, *args)

        with Provider._cache_lock:
            cached = Provider._cache.get(key)

            if cached:
                if time.monotonic() - cached[0] < self.cache_ttl:
                    return True, deepcopy(cached[1])

                Provider._cache.pop(key, None)

        return False, None

    # Stores a provider result in memory
    def _set_cache(self, method: str, value, *args):
        key = self._cache_key(method, *args)
        now = time.monotonic()

        with Provider._cache_lock:

            # Remove expired entries opportunistically
            for cache_key, cached in list(Provider._cache.items()):
                if now - cached[0] >= self.cache_ttl:
                    Provider._cache.pop(cache_key, None)

            Provider._cache[key] = (now, deepcopy(value))

        return value

    @staticmethod
    def _stable_versions(versions):
        return [version for version in versions if is_semver(version) and "-" not in version]

# Abstracts provider-specific network operations for downloadable items
class AddonProvider(Provider):

    # Provider name and supported server types
    name:            str
    project_url:     str
    project_api:     str = None

    def __init__(self, server_properties: dict):
        self._server = server_properties
        self.server_type = manager.parse_server_type(self._server['type'])

    # Internal helper to convert server type into search filters
    def _get_loader_types(self) -> list[str]:
        return [self.server_type]

    # Returns list of addon objects according to search
    # Query --> AddonWebObject
    def search_addons(self, query: str, _log: bool = False, *args):
        results = []
        cache_id = query.strip().lower()
        cache_hit, results = self._get_cache('search', cache_id)

        log_tag = f"'{query.strip()}' ({self.server_type})"
        if _log: self._send_log(f"searching for {log_tag}...", 'info')

        success = cache_hit

        if not cache_hit:
            try:
                results = self.search(query)
                success = True

            except Exception as e:
                self._send_log(f"error searching for {log_tag}: {constants.format_traceback(e)}", 'error')

        if results:

            # Fingerprint addon with the current provider
            for addon in results:
                addon.provider = self.name

            debug_only = f':\n{results}' if constants.debug else ''
            if _log: self._send_log(f"found {len(results)} add-on(s) for {log_tag}{debug_only}", 'info')

        elif _log:
            self._send_log(f"no add-ons were found for {log_tag}", 'info')

        if not cache_hit and success:
            self._set_cache('search', results, cache_id)

        return results

    # Provider-specific search implementation
    def search(self, query: str):
        raise NotImplementedError

    # Returns advanced addon object properties
    # AddonWebObject
    def get_addon_info(self, addon: AddonWebObject):

        # For cleaning up description formatting
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+",
            flags = re.UNICODE
        )

        if addon.supported == "unknown" or addon.description is None:
            cache_id = str(addon.id or addon.name).strip().lower()
            cache_hit, page_content = self._get_cache('description', cache_id)

            if not cache_hit:
                page_content = self.get_description(addon) or ''
                self._set_cache('description', page_content, cache_id)

            description = emoji_pattern.sub(r'', page_content).replace("*", "").replace("#", "").replace('&nbsp;', ' ')
            description = '\n' + re.sub(r'(\n\s*)+\n', '\n\n', re.sub(r'<[^>]*>', '', description)).strip()
            description = re.sub(r'!?\[?\[(.+?)\]\(.*\)', lambda x: x.group(1), description).replace("![", "")
            description = re.sub(r'\]\(*.+\)', '', description)

            addon.description = description

        if addon.supported == "unknown":
            server_version = self._server["version"]
            addon.supported = "yes" if server_version in addon.versions else "no"

        return addon

    # Returns provider-specific description content
    def get_description(self, addon: AddonWebObject):
        raise NotImplementedError

    # Cleans up addon version from title
    def format_version(self, raw_version: str):
        try:
            raw_version = re.sub(r'(\[|\(|\{).*(\)|\]|\})', '', raw_version.lower())
            raw_version = raw_version.replace('beta', '.').replace('alpha', '.').replace('u', '.').replace('b','.').replace('a', '.')
            raw_version = re.sub("[^0-9|.]", "", raw_version)
            raw_version = re.search(r'\d+(\.\d+)+', raw_version).group(0)
        except: raw_version = None
        return raw_version

    # Return the latest available supported download link
    # - compat_mode: allows older addon versions to be selected as a download if the Minecraft version is not available
    # - force_available: if the server is older than the oldest addon version, use the oldest one available
    # AddonWebObject
    def get_addon_url(self, addon: AddonWebObject, compat_mode=True, force_available=False):

        # Skip if addon doesn't exist for some reason
        if not addon:
            return False

        addon.provider   = self.name
        addon_list       = []
        selected_addon   = None
        selected_version = None
        server_version   = self._server["version"]
        log_tag          = f"'{addon.name}' ({addon.type} {server_version})"

        self._send_log(f"retrieving download link for {log_tag}...\ncompat_mode: {compat_mode}")

        try: addon_list = self.get_addon_versions(addon)
        except Exception as e:
            self._send_log(f"error retrieving download link for {log_tag}: {constants.format_traceback(e)}", 'error')

        # Providers return releases newest-first, so the first exact match is latest
        for available_addon in addon_list:
            if server_version in available_addon.versions:
                selected_addon = available_addon
                selected_version = server_version
                addon.supported = "yes"
                break

        # If an exact release is unavailable, find the closest older Minecraft version
        if not selected_addon and compat_mode:
            compatible_addons = []

            for available_addon in addon_list:
                for version in self._stable_versions(available_addon.versions):
                    if constants.version_check(server_version, ">=", version):
                        compatible_addons.append((version, available_addon))

            if compatible_addons:
                def _key(item):
                    return tuple(map(int, item[0].split(".")))

                # Stable sorting keeps provider order for releases supporting the same version
                selected_version, selected_addon = sorted(compatible_addons, key=_key, reverse=True)[0]
                addon.supported = "no"

        # If the server predates every supported version, use the oldest release
        if not selected_addon and force_available and addon_list:
            for available_addon in reversed(addon_list):
                versions = self._stable_versions(available_addon.versions)
                if versions:
                    selected_addon = available_addon
                    selected_version = sorted(versions, key=lambda v: tuple(map(int, v.split("."))))[0]
                    addon.supported = "no"
                    break

        if selected_addon:
            addon.download_url = selected_addon.download_url
            addon.download_version = selected_version
            addon.addon_version = selected_addon.addon_version
            addon.release_type = selected_addon.release_type
            self._send_log(f"found download for {log_tag}:\n{addon.download_url}")

        else:
            addon.download_url = None
            addon.download_version = None
            addon.addon_version = None
            addon.release_type = None
            self._send_log(f"no download was found for {log_tag}", 'error')

        return addon

    # Returns every available release as AddonWebObjects
    def get_addon_versions(self, addon: AddonWebObject, server_version=None, latest=False):
        cache_id = str(addon.id or addon.name).strip().lower()
        version_id = str(server_version or '').strip().lower()

        cache_hit, versions = self._get_cache('versions', cache_id, version_id, latest)
        if cache_hit:
            return versions

        versions = self._get_addon_versions(addon, server_version, latest)
        self._set_cache('versions', versions, cache_id, version_id, latest)

        return versions

    # Provider-specific version implementation
    def _get_addon_versions(self, addon: AddonWebObject):
        raise NotImplementedError

    # Parse local add-on information to find a downloadable update
    # AddonFileObject or str --> AddonWebObject
    def get_update_url(self, addon: AddonFileObject or str):
        new_addon = self._find_addon(addon)

        if not new_addon:
            return None

        versions = self.get_addon_versions(new_addon, self._server['version'], latest=True)
        if versions:
            versions[0].supported = 'yes'
            return versions[0]

        return None

    # Searches and returns downloadable addon
    # str or AddonFileObject --> AddonWebObject
    def _find_addon(self, addon: AddonFileObject or str):
        file_addon = addon if getattr(addon, 'addon_object_type', None) == 'file' else None

        # Removes punctuation/casing differences from IDs, names, and authors
        def normalize(value):
            return re.sub(r'[^a-z0-9]+', '', str(value or '').strip().lower())

        def similarity(first, second):
            if not first or not second:
                return 0

            return SequenceMatcher(None, first, second).ratio()

        # Local files are searched through their manifest ID, filename, and display name
        if file_addon:
            queries = []
            file_name = os.path.splitext(os.path.basename(file_addon.path))[0]
            trusted_queries = [normalize(file_addon.id), normalize(file_name)]

            for query in [file_addon.id, file_name, file_addon.name]:
                query = str(query or '').strip()

                if query and query.lower() not in [item.lower() for item in queries]:
                    queries.append(query)

        # Preserve normal string lookup behavior
        else:
            query = str(addon or '').strip()
            queries = [query] if query else []
            trusted_queries = []

        if not queries:
            return False

        addon_results = []

        # Merge and deduplicate search results from every useful local identifier
        for query in queries:
            query_results = self.search_addons(query)
            for result in query_results:
                if result not in addon_results:
                    addon_results.append(result)

            # An exact manifest-ID or filename project match doesn't need further fuzzy searches
            if file_addon and normalize(query) in trusted_queries:
                exact_results = [
                    result for result in addon_results
                    if normalize(query) in [normalize(result.id), normalize(result.name)]
                ]

                if exact_results:
                    addon_results = exact_results
                    break

        new_addon = None
        search_match = False

        if addon_results:

            # Existing string behavior: return the closest name/ID result
            if not file_addon:
                normalized_query = normalize(queries[0])

                def match_score(result):
                    result_id = normalize(result.id)
                    result_name = normalize(result.name)

                    if result_id and result_id == normalized_query:
                        return 1000

                    return max(
                        similarity(result_id, normalized_query),
                        similarity(result_name, normalized_query)
                    )

                new_addon = sorted(addon_results, key=match_score, reverse=True)[0]
                search_match = True

            # AddonFileObject behavior: compare all locally parsed identity fields
            else:
                addon_id = normalize(file_addon.id)
                addon_name = normalize(file_addon.name)
                addon_author = normalize(file_addon.author)

                def match_score(result):
                    result_id = normalize(result.id)
                    result_name = normalize(result.name)
                    result_author = normalize(result.author)

                    id_similarity = max(
                        similarity(addon_id, result_id),
                        similarity(addon_id, result_name)
                    )

                    name_similarity = max(
                        similarity(addon_name, result_name),
                        similarity(addon_name, result_id)
                    )

                    author_similarity = similarity(
                        addon_author,
                        result_author
                    )

                    exact_id     = bool(addon_id and addon_id in [result_id, result_name])
                    exact_name   = bool(addon_name and addon_name in [result_name, result_id])
                    exact_author = bool(
                        addon_author
                        and result_author
                        and addon_author == result_author
                    )

                    score = (
                        (id_similarity * 4)
                        + (name_similarity * 3)
                        + author_similarity
                    )

                    if exact_id:     score += 4
                    if exact_name:   score += 3
                    if exact_author: score += 1

                    # Require a deliberate identity relationship for automatic matching
                    valid_match = bool(
                        exact_id
                        or (id_similarity >= 0.85 and name_similarity >= 0.75)
                        or (id_similarity >= 0.95 and not addon_name)
                        or (name_similarity >= 0.95 and not addon_id)
                        or (
                            exact_name
                            and (
                                not addon_author
                                or not result_author
                                or author_similarity >= 0.75
                            )
                        )
                        or (
                            name_similarity >= 0.9
                            and (
                                not addon_author
                                or not result_author
                                or author_similarity >= 0.75
                            )
                        )
                    )

                    return score, valid_match

                scored_results = []

                for result in addon_results:
                    score, valid_match = match_score(result)
                    scored_results.append((result, score, valid_match))

                scored_results.sort(key=lambda result: result[1], reverse=True)
                valid_results = [result for result in scored_results if result[2]]
                if valid_results:
                    new_addon = valid_results[0][0]
                    search_match = True

        # Preserve the existing direct-slug fallbacks when search cannot identify it
        if file_addon and not new_addon:
            project_ids = []

            if file_addon.id:
                project_ids.append(str(file_addon.id).strip())

            if file_addon.name:
                filtered_name = re.sub(r'[^A-Za-z _+-]+', '', file_addon.name)
                filtered_name = re.sub(r'\s+', '-', filtered_name).lower()

                if filtered_name and filtered_name.lower() not in [project_id.lower() for project_id in project_ids]:
                    project_ids.append(filtered_name)

            for project_id in project_ids:
                potential_url = self.project_url + project_id
                lookup_url = (self.project_api or self.project_url) + project_id

                try:
                    response = constants.get_url(lookup_url, return_response=True)
                    if response.status_code in [200, 302]:
                        new_addon = AddonWebObject(
                            file_addon.name,
                            self.server_type,
                            file_addon.author,
                            file_addon.subtitle,
                            potential_url,
                            project_id,
                            None
                        )
                        break

                except Exception:
                    continue

        if not new_addon:
            return False

        # Expand project metadata for searches
        # File resolution only needs release info
        if search_match and not file_addon:
            new_addon = self.get_addon_info(new_addon)

        new_addon.provider = self.name
        return new_addon

    # Public interface
    def find_addon(self, addon: AddonFileObject or str):
        new_addon = self._find_addon(addon)

        if new_addon:
            return self.get_addon_url(new_addon)

        return False


# Handles mods/plugins from the CurseForge API
class CurseForgeProvider(AddonProvider):
    name = 'curseforge'
    project_url = 'https://www.curseforge.com/minecraft/mc-mods/'
    project_api = 'https://curseforge.auto-mcs.com/project/'

    loader_types = {
        'forge':    1,
        'fabric':   4,
        'quilt':    5,
        'neoforge': 6
    }

    release_types = {
        1: 'release',
        2: 'beta',
        3: 'alpha'
    }

    def __init__(self, server_properties: dict):
        super().__init__(server_properties)

        if self.server_type == 'bukkit':
            self.project_url = 'https://www.curseforge.com/minecraft/bukkit-plugins/'

    # CurseForge API responses should not be cached
    def _get_cache(self, method: str, *args):
        return False, None

    def _set_cache(self, method: str, value, *args):
        return value

    # Internal helper to convert server type into search filters
    def _get_loader_types(self):
        if self.server_type == 'bukkit':
            return []

        if self.server_type == 'quilt':
            return ['quilt', 'fabric']

        return [self.server_type]

    # Cleans up CurseForge Minecraft versions
    @staticmethod
    def _format_game_version(raw_version):
        if not isinstance(raw_version, str):
            return None

        match = re.search(r'\d+(?:\.\d+)+', raw_version)
        return match.group(0) if match else None

    # Extracts the add-on version without confusing it with the Minecraft version
    @staticmethod
    def _format_addon_version(data, game_versions):
        raw_version = str(data.get('displayName') or data.get('fileName') or '')
        version_list = re.findall(r'\d+(?:\.\d+)+', raw_version)

        if not version_list:
            return None

        # Prefer a version which isn't just the supported Minecraft version
        for version in version_list:
            if version not in game_versions:
                return version

        # Some older projects use the Minecraft version as their own release version
        return version_list[0]

    # Grab every add-on from search result and return results dict
    def search(self, query: str):
        results = []
        addon_type = 'plugin' if self.server_type == 'bukkit' else 'mod'
        search_url = self.project_url

        url = f'https://curseforge.auto-mcs.com/search?type={addon_type}&q={query}&page_size=50'
        page_content = constants.get_url(url, return_response=True).json()

        loader_ids = [
            self.loader_types[loader]
            for loader in self._get_loader_types()
            if loader in self.loader_types
        ]

        for mod in page_content.get('data', []):

            if not mod.get('isAvailable', True):
                continue

            indexes = mod.get('latestFilesIndexes') or []

            # Filter projects which have no releases for this loader
            if loader_ids and indexes:
                loader_indexes = [
                    index for index in indexes
                    if index.get('modLoader') in loader_ids
                ]

                if not loader_indexes:
                    continue

            else:
                loader_indexes = indexes

            name = mod['name']
            author = (mod.get('authors') or [{}])[0].get('name', '')
            subtitle = str(mod.get('summary') or '').split("\n", 1)[0]
            file_name = mod['slug']
            link = (mod.get('links') or {}).get('websiteUrl') or search_url + file_name
            project_id = str(mod['id'])

            if link:
                addon_obj = AddonWebObject(name, self.server_type, author, subtitle, link, project_id, None)

                logo = mod.get('logo') or {}
                addon_obj.icon_url = logo.get('thumbnailUrl') or logo.get('url')

                versions = []
                for index in loader_indexes:
                    version = self._format_game_version(index.get('gameVersion'))

                    if version and version not in versions:
                        versions.append(version)

                addon_obj.versions = versions
                results.append(addon_obj)

        return results

    # Run specific actions for CurseForge mods/plugins
    def get_description(self, addon: AddonWebObject):

        # Find add-on information
        file_link = f'{self.project_api}{addon.id}/description'
        page_content = constants.get_url(file_link, return_response=True).json()
        return page_content.get('data', '')

    # Returns every available CurseForge release as AddonWebObjects
    def _get_addon_versions(self, addon: AddonWebObject, server_version=None, latest=False):
        addon_list = []

        # CurseForge allows up to 50 results per page
        loop_limit   = 20
        page_size    = 50
        current_page = 0
        total        = 0
        retrieved    = -1

        loader_types = self._get_loader_types()
        loader_type = loader_types[0] if loader_types else None

        # Get data from the API per page
        def get_content(page: int = 0, loader=None):
            if loader is None:
                loader = loader_type

            page_url = f'{self.project_api}{addon.id}/files?page_size={page_size}&index={page_size * page}'

            if server_version:
                page_url += f'&version={server_version}'

            if loader:
                page_url += f'&loader={loader}'

            return constants.get_url(page_url, return_response=True).json()

        # Process a single page
        def process_page(page_content):
            nonlocal retrieved, page_size, total, current_page

            files      = page_content.get('data', [])
            pagination = page_content.get('pagination', {})

            if files:

                # Learn server provided pagination on first load
                if retrieved < 0:
                    page_size = pagination.get('pageSize', page_size)
                    total     = pagination.get('totalCount') or len(files)
                    retrieved = 0

                # Ensure the newest releases are processed first
                files.sort(key=lambda data: data.get('fileDate', ''), reverse=True)

                # Create an AddonWebObject for every release
                for data in files:

                    if not data.get('isAvailable', True):
                        continue

                    download_url = data.get('downloadUrl')

                    # Respect projects/files which disable third-party distribution
                    if not download_url:
                        continue

                    versions = []

                    for version in data.get('gameVersions', []):
                        version = self._format_game_version(version)

                        if version and version not in versions:
                            versions.append(version)

                    if not versions:
                        continue

                    addon_version = self._format_addon_version(data, versions)

                    new_addon = deepcopy(addon)
                    new_addon.versions = versions
                    new_addon.download_url = download_url
                    new_addon.download_version = None
                    new_addon.addon_version = addon_version
                    new_addon.release_type = self.release_types.get(data.get('releaseType'))

                    addon_list.append(new_addon)

                retrieved += len(files)
                current_page += 1

            # Stop on no results
            else:
                raise StopIteration


        # First page sync to learn pagination
        try:
            first_page = get_content(current_page)
            process_page(first_page)
        except StopIteration:
            pass

        # Quilt can generally use Fabric mods as a fallback
        if not addon_list and self.server_type == 'quilt':
            loader_type = 'fabric'
            current_page = 0
            total = 0
            retrieved = -1

            try:
                first_page = get_content(current_page, loader_type)
                process_page(first_page)
            except StopIteration:
                pass

        # Update lookups only need the newest supported release
        if latest:
            return addon_list[:1]

        # Load remaining pages via thread pool merged in order
        if 0 <= retrieved < total and current_page < loop_limit:
            num_pages = math.ceil(total / page_size) if page_size else 0
            last_page = min(loop_limit, num_pages)

            if last_page > current_page:
                pages = range(current_page, last_page)

                with ThreadPoolExecutor(max_workers=2) as pool:
                    for page_content in pool.map(get_content, pages):
                        try: process_page(page_content)
                        except StopIteration:
                            break

        return addon_list


# Handles plugins from the Hangar API
class HangarProvider(AddonProvider):
    name = 'hangar'
    project_url = 'https://hangar.papermc.io/api/v1/projects/'

    def search(self, query: str):
        results = []

        # filter-sort=5 is filtered by number of downloads
        search_url = "https://hangar.papermc.io/"

        # Grab every addon from search result and return results dict
        url = f'https://hangar.papermc.io/api/v1/projects?query={query}&limit=100'
        page_content = constants.get_url(url, return_response=True).json()

        for plugin in page_content['result']:
            if 'supportedPlatforms' in plugin and 'PAPER' in plugin['supportedPlatforms']:
                name = plugin['name']
                author = plugin['namespace']['owner']
                subtitle = plugin['description'].split("\n", 1)[0]
                file_name = plugin['namespace']['slug']
                link = search_url + f'{author}/{file_name}'

                if link:
                    addon_obj = AddonWebObject(name, self.server_type, author, subtitle, link, file_name, None)
                    addon_obj.icon_url = plugin.get('avatarUrl')
                    versions = [version for version in reversed(plugin['supportedPlatforms']['PAPER']) if isinstance(version, str)]
                    addon_obj.versions = versions
                    addon_obj.description = plugin['mainPageContent']
                    self.get_addon_info(addon_obj)
                    results.append(addon_obj)

        return results

    # Run specific actions for Hangar plugins
    def get_description(self, addon: AddonWebObject):
        description = ''

        if addon.description:

            # Format existing addon description from "mainPageContent"
            description = addon.description

        return description

    # Returns every available Bukkit release as AddonWebObjects
    def _get_addon_versions(self, addon: AddonWebObject, server_version=None, latest=False):
        addon_list = []

        # Value can be 1-25 (API enforced)
        loop_limit   = 25
        page_size    = 25
        current_page = 1
        total        = 0
        retrieved    = -1

        # Get data from the API per page
        def get_content(page: int = 1):
            page_url = f'https://hangar.papermc.io/api/v1/projects/{addon.id}/versions?limit={page_size}'
            if server_version: page_url += f'&platform=PAPER&platformVersion={server_version}'
            if page < 1:       page = 1
            else:              page_url += f'&offset={page_size * (page - 1)}'
            return constants.get_url(page_url, return_response=True).json()

        # Process a single page
        def process_page(page_content):
            nonlocal retrieved, page_size, total, current_page

            results    = page_content.get('result', [])
            pagination = page_content.get('pagination', {})
            if pagination and results:

                # Learn server provided pagination on first load
                if not (retrieved and total):
                    page_size = pagination.get('limit', page_size)
                    total     = pagination.get('count') or pagination.get('total') or len(results)
                    retrieved = 0

                # Create an AddonWebObject for every release
                for data in results:
                    paper = (data.get('downloads') or {}).get('PAPER')
                    if not paper:
                        continue

                    url = paper.get('downloadUrl') or paper.get('externalUrl')
                    if not url:
                        continue

                    versions = [version for version in (data.get('platformDependencies') or {}).get('PAPER', []) if isinstance(version, str)]
                    if not versions:
                        continue

                    new_addon = deepcopy(addon)
                    new_addon.versions = versions
                    new_addon.download_url = url
                    new_addon.download_version = None
                    new_addon.addon_version = self.format_version(data.get('name', ''))

                    channel = data.get('channel') or {}
                    new_addon.release_type = 'beta' if 'UNSTABLE' in (channel.get('flags') or []) else 'release'

                    addon_list.append(new_addon)

                retrieved += len(results)
                current_page += 1

            # Stop on no results
            else: raise StopIteration


        # First page sync to learn pagination
        try:
            first_page = get_content(current_page)
            process_page(first_page)
        except StopIteration:
            pass

        # Update lookups only need the newest supported release
        if latest: return addon_list[:1]

        # Load remaining pages via thread pool merged in order
        if retrieved < total and current_page < loop_limit:
            num_pages = math.ceil(total / page_size) if page_size else 0
            last_page = min(loop_limit, num_pages)

            if last_page >= current_page:
                pages = range(current_page, last_page + 1)

                with ThreadPoolExecutor(max_workers=2) as pool:
                    for page_content in pool.map(get_content, pages):
                        try: process_page(page_content)
                        except StopIteration:
                            break

        return addon_list


# Handles mods from the Modrinth API
class ModrinthProvider(AddonProvider):
    name = 'modrinth'
    project_url = 'https://modrinth.com/mod/'
    project_api = 'https://api.modrinth.com/v2/project/'

    # Internal helper to convert server type into search filters
    def _get_loader_types(self):
        if self.server_type == 'bukkit':
            return ['bukkit', 'spigot', 'paper', 'purpur', 'folia']

        if self.server_type == 'quilt':
            return ['quilt', 'fabric']

        return [self.server_type]

    # If 'server_type' is forge, fabric, quilt, or neoforge
    # Use Modrinth provider
    def search(self, query: str):
        results = []
        search_url = "https://modrinth.com/mod/"

        # Grab every addon from search result and return results dict
        loader_facets = ','.join([f'"categories:{loader}"' for loader in self._get_loader_types()])
        url = (
            'https://api.modrinth.com/v2/search'
            f'?facets=[[{loader_facets}],'
            '["server_side:optional","server_side:required"]]'
            f'&limit=100&query={query}'
        )

        page_content = constants.get_url(url, return_response=True).json()

        for mod in page_content['hits']:
            project_types = (mod.get('all_project_types') or [mod.get('project_type')])
            if any(project_type in ['mod', 'plugin'] for project_type in project_types):
                name = mod['title']
                author = mod['author']
                subtitle = mod['description'].split("\n", 1)[0]
                file_name = mod['slug']
                link = search_url + file_name

                if link:
                    addon_obj = AddonWebObject(name, self.server_type, author, subtitle, link, file_name, None)
                    addon_obj.icon_url = mod.get('icon_url')
                    versions = [version for version in reversed(mod['versions']) if isinstance(version, str)]
                    addon_obj.versions = versions
                    results.append(addon_obj)

        return results

    # Run specific actions for Modrinth mods
    def get_description(self, addon: AddonWebObject):

        # Find addon information
        file_link = f"https://api.modrinth.com/v2/project/{addon.id}"
        page_content = constants.get_url(file_link, return_response=True).json()
        return page_content['body']

    # Returns every available mod release as AddonWebObjects
    def _get_addon_versions(self, addon: AddonWebObject, server_version=None, latest=False):
        addon_list = []
        loader_types = json.dumps(self._get_loader_types(), separators=(',', ':'))
        game_versions = (
            f'&game_versions={json.dumps([server_version], separators=(",", ":"))}'
            if server_version
            else ''
        )

        # Iterate through every available version
        try:
            file_link = f'https://api.modrinth.com/v2/project/{addon.id}/version?loaders={loader_types}{game_versions}&include_changelog=false'
            page_content = constants.get_url(file_link, return_response=True).json()

        # In case the ID is a problem for whatever reason
        except json.JSONDecodeError:
            file_link = f'https://api.modrinth.com/v2/project/{constants.sanitize_name(addon.name).lower()}/version?loaders={loader_types}{game_versions}&include_changelog=false'
            page_content = constants.get_url(file_link, return_response=True).json()

        # Workaround for Fabric mods on Quilt
        if not page_content and addon.type == 'quilt':
            file_link = f'https://api.modrinth.com/v2/project/{addon.id}/version?loaders=["fabric"]{game_versions}&include_changelog=false'
            page_content = constants.get_url(file_link, return_response=True).json()

        # Ensure the first compatible release is the newest
        page_content.sort(key=lambda data: data.get('date_published', ''), reverse=True)

        # Create an AddonWebObject for every release
        for data in page_content:
            files = data.get('files', [])
            if not files:
                continue

            file = next((f for f in files if f.get('primary')), files[0])

            versions = [version for version in data.get('game_versions', []) if isinstance(version, str)]
            if not versions:
                continue

            # Remove supported Minecraft versions before parsing the add-on version
            raw_version = data.get('version_number', '').split('+', 1)[0]
            for game_version in sorted(data.get('game_versions', []), key=len, reverse=True):
                raw_version = raw_version.replace(game_version, '')

            addon_version = self.format_version(raw_version)

            new_addon = deepcopy(addon)
            new_addon.versions = versions
            new_addon.download_url = file['url']
            new_addon.download_version = None
            new_addon.addon_version = addon_version
            new_addon.release_type = data.get('version_type')

            addon_list.append(new_addon)

            # Skip if checking for updates
            if latest: break

        return addon_list


# Abstracts provider-specific network operations for downloadable modpacks
class ModpackProvider(Provider):

    # Provider name
    name: str

    # Returns list of modpack objects according to search
    # Query --> ModpackWebObject
    def search_modpacks(self, query: str, _log: bool = True, *args):
        results = []
        cache_id = query.strip().lower()
        cache_hit, results = self._get_cache('search', cache_id)

        log_tag = f"'{query.strip()}'"
        if _log: self._send_log(f"searching for {log_tag}...", 'info')

        success = cache_hit

        if not cache_hit:
            try:
                results = self.search(query)
                success = True

            except Exception as e:
                self._send_log(f"error searching for {log_tag}: {constants.format_traceback(e)}", 'error')

        if results:

            # Fingerprint modpack with the current provider
            for modpack in results:
                modpack.provider = self.name

            results = sorted(results, key=lambda x: x.score, reverse=True)
            debug_only = f':\n{results}' if constants.debug else ''
            if _log: self._send_log(f"found {len(results)} modpack(s) for {log_tag}{debug_only}", 'info')

        else:
            self._send_log(f"no modpacks were found for {log_tag}", 'info')

        if not cache_hit and success:
            self._set_cache('search', results, cache_id)

        return results

    # Provider-specific search implementation
    def search(self, query: str):
        raise NotImplementedError

    # Returns advanced modpack object properties
    # ModpackWebObject
    def get_modpack_info(self, modpack: ModpackWebObject, *args):

        # For cleaning up description formatting
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+",
            flags = re.UNICODE
        )

        cache_id = str(modpack.id or modpack.name).strip().lower()
        cache_hit, page_content = self._get_cache('description', cache_id)

        if not cache_hit:
            page_content = self.get_description(modpack) or ''
            self._set_cache('description', page_content, cache_id)

        description = emoji_pattern.sub(r'', page_content).replace("*","").replace("#","").replace('&nbsp;', ' ')
        description = '\n' + re.sub(r'(\n\s*)+\n', '\n\n', re.sub(r'<[^>]*>', '', description)).strip()
        description = re.sub(r'!?\[?\[(.+?)\]\(.*\)', lambda x: x.group(1), description).replace("![","")
        description = re.sub(r'\]\(*.+\)', '', description)

        modpack.description = description
        modpack.supported = "yes"

        return modpack

    # Returns provider-specific description content
    def get_description(self, modpack: ModpackWebObject):
        raise NotImplementedError

    # Return the latest available download link
    # ModpackWebObject
    def get_modpack_url(self, modpack: ModpackWebObject, *args):
        if not modpack:
            return False

        versions = self.get_modpack_versions(modpack)

        if versions:
            latest = next((version for version in versions if version.download_url), None)

            if latest:
                modpack.download_url = latest.download_url
                modpack.download_version = latest.download_version
                modpack.addon_version = latest.addon_version
                modpack.release_type = latest.release_type

                return modpack

        return False

    # Returns every available release as ModpackWebObjects
    def get_modpack_versions(self, modpack: ModpackWebObject):
        cache_id = str(modpack.id or modpack.name).strip().lower()
        cache_hit, versions = self._get_cache('versions', cache_id)

        if cache_hit:
            return versions

        versions = self._get_modpack_versions(modpack)
        self._set_cache('versions', versions, cache_id)

        return versions

    # Provider-specific version implementation
    def _get_modpack_versions(self, modpack: ModpackWebObject):
        raise NotImplementedError

    # Checks if an update is available for an installed modpack
    def check_for_updates(self, name: str):
        try: return self.check_update(name)
        except Exception as e:
            self._send_log(f"failed to check for updates to '{name}': {constants.format_traceback(e)}", 'error')
        return None

    # Provider-specific update check
    def check_update(self, name: str):
        raise NotImplementedError

    # Downloads a provider modpack archive
    def download_modpack(self, name: str, url: str, progress_func=None):
        def hook(a, b, c):
            if progress_func:
                progress_func(round(100 * a * b / c))

        file_name = f"{constants.sanitize_name(name)}.{url.rsplit('.', 1)[-1]}"
        return constants.download_url(url, file_name, paths.downloads, hook)


# Handles modpacks from the Modrinth API
class ModrinthModpackProvider(ModpackProvider):
    name = 'modrinth'

    # Returns the provider version ID for a local .mrpack
    def get_file_version(self, file_path: str):
        try:
            file_hash = hashlib.sha512()
            with open(file_path, 'rb') as file:
                for chunk in iter(lambda: file.read(1048576), b''):
                    file_hash.update(chunk)

            file_link = f'https://api.modrinth.com/v2/version_file/{file_hash.hexdigest()}?algorithm=sha512'
            response = constants.get_url(file_link, return_response=True)

            if response.status_code == 200:
                return response.json()['id']

        except Exception as e:
            self._send_log(f"failed to resolve version for '{os.path.basename(file_path)}': {constants.format_traceback(e)}", 'warning')

        return None

    # Grab every modpack from search result and return results dict
    def search(self, query: str):
        url = f'https://api.modrinth.com/v2/search?facets=[["project_type:modpack"]]&limit=100&query={query}'
        results = []
        page_content = constants.get_url(url, return_response=True).json()

        for mod in page_content['hits']:

            # Ignore modpacks which explicitly don't support dedicated servers
            if mod.get('server_side') == 'unsupported':
                continue

            name = mod['title']
            author = mod['author']
            subtitle = mod['description'].split("\n", 1)[0]
            project_id = mod['project_id']
            link = f"https://modrinth.com/modpack/{mod['slug']}"
            score = constants.similarity(query.strip().lower(), name.strip().lower())

            if link:
                modpack_obj = ModpackWebObject(name, 'modpack', author, subtitle, link, project_id, None)
                modpack_obj.icon_url = mod.get('icon_url')
                modpack_obj.score = score
                versions = [v for v in reversed(mod['versions']) if (is_semver(v) and "-" not in v)]
                modpack_obj.versions = sorted(versions, key=lambda x: tuple(map(int, x.split("."))), reverse=True)
                results.append(modpack_obj)

        return results

    # Find modpack information
    def get_description(self, modpack: ModpackWebObject):
        file_link = f"https://api.modrinth.com/v2/project/{modpack.id}"
        return constants.get_url(file_link, return_response=True).json()['body']

    # Returns every available modpack release as ModpackWebObjects
    def _get_modpack_versions(self, modpack: ModpackWebObject):
        modpack_list = []
        file_link = f'https://api.modrinth.com/v2/project/{modpack.id}/version?include_changelog=false'
        page_content = constants.get_url(file_link, return_response=True).json()

        # Ensure the newest release is first
        page_content.sort(key=lambda data: data.get('date_published', ''), reverse=True)

        def _valid_filename(filename: str):
            return 'server' in filename.lower() and filename.lower().endswith(('.zip', '.mrpack'))

        for data in page_content:
            files = data.get('files', [])
            if not files:
                continue

            # Prefer a dedicated server archive
            file = next((
                file for file in files
                if _valid_filename(file.get('filename', '')) and file.get('url')
            ), None)

            # Otherwise, use the primary archive
            if not file:
                file = next((file for file in files if file.get('primary') and file.get('url')), None)

            # Otherwise, use the first available download
            if not file:
                file = next((file for file in files if file.get('url')), None)

            if not file:
                continue

            new_modpack = deepcopy(modpack)
            new_modpack.versions = data.get('game_versions', [])
            new_modpack.download_url = file['url']
            new_modpack.download_version = data['id']
            new_modpack.addon_version = data['version_number']
            new_modpack.release_type = data.get('version_type')
            modpack_list.append(new_modpack)

        return modpack_list

    # Checks if an installed Modrinth pack has an update
    def check_update(self, name: str):
        index_name = f'{"modrinth.index.json" if constants.os_name == "windows" else ".modrinth.index.json"}'
        index = os.path.join(manager.server_path(name), index_name)

        if not os.path.isfile(index):
            return None

        if constants.os_name == 'windows':
            constants.run_proc(f'attrib -H "{index}"')

        try:
            with open(index, 'r', encoding='utf-8', errors='ignore') as f:
                index_data = json.loads(f.read())

        finally:
            if constants.os_name == 'windows':
                constants.run_proc(f'attrib +H "{index}"')

        current_id = str(index_data.get('modrinthVersionId') or '')
        current_version = str(index_data.get('versionId') or '')
        query = str(index_data.get('name') or '').strip()

        if not current_version or not query:
            return None

        def normalize(value):
            return re.sub(r'[^a-z0-9]+', '', str(value or '').lower())

        online_modpack = None

        # Resolve exact project from the provider version ID
        if current_id:
            try:
                version_data = constants.get_url(f'https://api.modrinth.com/v2/version/{current_id}', return_response=True).json()
                project_id = version_data.get('project_id')
                if project_id:
                    online_modpack = ModpackWebObject(query, 'modpack', '', '', f'https://modrinth.com/project/{project_id}', project_id, None)

            except: pass

        # Progressively remove trailing version/release text until the project itself matches
        while query and not online_modpack:
            results = self.search_modpacks(query, _log=False)
            query_id = normalize(query)

            for modpack in results:
                name_id = normalize(modpack.name)
                slug_id = normalize(modpack.url.rsplit('/', 1)[-1])

                if query_id in [name_id, slug_id]:
                    online_modpack = modpack
                    break

            if not online_modpack:
                query = query.rsplit(' ', 1)[0] if ' ' in query else ''

        if not online_modpack:
            return None

        versions = self.get_modpack_versions(online_modpack)

        if not versions:
            return None

        # Prefer the provider version ID
        current = next((
            modpack for modpack in versions
            if current_id == str(modpack.download_version)
        ), None) if current_id else None

        # Legacy fallback to the pack's versionId
        if not current:
            current = next((
                modpack for modpack in versions
                if current_version in [str(modpack.download_version), str(modpack.addon_version)]
            ), None)

        # Don't invent an update if the installed release can't be identified
        if not current:
            return None

        latest = next((modpack for modpack in versions if modpack.download_url), None)
        if not latest:
            return None

        if current.download_version != latest.download_version:
            return latest

        return None


# Map for providers per server type
addon_provider_registry = {
    'vanilla':     [],

    'craftbukkit': [HangarProvider, ModrinthProvider, CurseForgeProvider],
    'spigot':      [HangarProvider, ModrinthProvider, CurseForgeProvider],
    'paper':       [HangarProvider, ModrinthProvider, CurseForgeProvider],
    'purpur':      [HangarProvider, ModrinthProvider, CurseForgeProvider],

    'forge':       [ModrinthProvider, CurseForgeProvider],
    'neoforge':    [ModrinthProvider, CurseForgeProvider],
    'fabric':      [ModrinthProvider, CurseForgeProvider],
    'quilt':       [ModrinthProvider, CurseForgeProvider]
}

# Default modpack provider for backwards-compatible module functions
modpack_provider = ModrinthModpackProvider()



# Server addon manager object for ServerManager()
class AddonManager():

    def _to_json(self):
        final_data = {
            k: getattr(self, k)
            for k in dir(self)
            if not (k.endswith('__') or callable(getattr(self, k)))
        }

        final_data.pop('_providers', None)
        final_data.pop('_update_lock', None)

        final_data['installed_addons'] = {
            k: [addon._to_json() for addon in v]
            for k, v in final_data['installed_addons'].items()
        }

        final_data['addon_queue'] = [
            addon._to_json()
            for addon in final_data['addon_queue']
        ]

        return final_data

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, f"'{self._server['name']}': {message}", level)

    def __init__(self, server_name: str):

        # Check if config file exists to determine new server status
        self._new_server = (not manager.server_path(server_name, constants.server_ini))

        try:
            self._server = dump_config(server_name, self._new_server)
            self._providers = {}
            self._addons_supported = False
            self.addon_queue: list[AddonObject] = []
            self.active_updates: list[str] = []
            self._update_lock = threading.RLock()
            self._set_providers()

            # New server add-ons are held in memory until Foundry installs them
            if self._new_server:
                self.installed_addons = {'enabled': [], 'disabled': []}
                self.geyser_support = False
                self._addon_hash = ''

            # Existing server add-ons are loaded from disk
            else:
                self.installed_addons = enumerate_addons(self._server)
                self.geyser_support = self.check_geyser()
                self._addon_hash = self._set_hash()

            # Setup filesystem paths
            self._set_paths()

            # Existing-server initialization only
            if not self._new_server:

                # Set addon hash if server is running
                try:
                    if self._server['name'] in constants.server_manager.running_servers:
                        constants.server_manager.running_servers[self._server['name']].run_data['addon-hash'] = deepcopy(self._addon_hash)
                except:
                    pass

                # Write addons to cache
                load_addon_cache(True)

            self._send_log('initialized AddonManager', 'info')

        except Exception as e:
            self._send_log(f'error initializing AddonManager: {constants.format_traceback(e)}')
            raise e

    # Loads AddonProviders based on server type
    def _set_providers(self, server_properties=None):
        server_properties = server_properties or self._server
        server_type = str(server_properties.get('type') or '').lower()
        provider_list = addon_provider_registry.get(server_type, [])
        loaded_list = [provider.__class__ for provider in self._providers.values()]

        # Recreate the registry only when the available providers change
        if loaded_list != provider_list:
            self._providers = {}

            for provider_class in provider_list:
                provider = provider_class(server_properties)
                self._providers[provider.name] = provider

            if self._providers:
                self._send_log(f"loaded add-on providers: {list(self._providers)}")

        # Reuse the loaded instances with the current target properties
        else:
            for provider in self._providers.values():
                provider._server = server_properties
                provider.server_type = manager.parse_server_type(server_type)

        self._addons_supported = bool(self._providers)
        return self._addons_supported

    # Runs an add-on method across the current providers
    def _run_providers(self, method, *args, single=False, **kwargs):
        addon = args[0] if args else None

        # Route provider-specific web objects directly
        if getattr(addon, 'addon_object_type', None) == 'web':
            provider = self._providers.get(getattr(addon, 'provider', None))

            if not provider:
                return False if single else []

            return getattr(provider, method)(*args, **kwargs)

        providers = list(self._providers.values())
        if not providers:
            return False if single else []

        def run(provider):
            try: return getattr(provider, method)(*args, **kwargs)
            except Exception as e:
                self._send_log(f"provider '{provider.name}' failed to run '{method}': {constants.format_traceback(e)}", 'error')

        with ThreadPoolExecutor(max_workers=len(providers)) as pool:
            result_list = list(pool.map(run, providers))

        addon_list = []

        for result in result_list:
            if isinstance(result, list):
                addon_list.extend(result)

            elif result:
                addon_list.append(result)

        return self._filter_addons(addon_list, addon, single)

    # Reload on type/version/name change
    def _refresh_config(self):
        server_properties = self._server

        try:
            from source.core.server.foundry import new_server_info

            # Use the active creation/update target when this manager owns it
            if new_server_info.get('addon_object') is self:
                server_properties = new_server_info

        except (ImportError, AttributeError):
            pass

        # New-server managers operate against the temporary server
        if self._new_server:
            self._server = dump_config(server_properties['name'], True)
            self._set_paths()

        self._set_providers(server_properties)
        return server_properties

    # Helper to define root filesystem paths
    def _set_paths(self):
        addon_folder = "plugins" if manager.parse_server_type(self._server['type']) == 'bukkit' else 'mods'
        self.addon_path = os.path.join(self._server['path'], addon_folder)
        self.disabled_addon_path = os.path.join(self._server['path'], "disabled-" + addon_folder)

    # Returns the value of the requested attribute (for remote)
    def _sync_attr(self, name):
        if name == '__all__':
            return self._to_json()
        return constants.sync_attr(self, name)

    # Filters duplicate provider results and returns the newest compatible object
    def _filter_addons(self, addon_list, query=None, single=False):
        addon_list = [addon for addon in addon_list if addon]
        if not addon_list: return False if single else []

        def _normalize(value):
            return re.sub(r'[^a-z0-9]+', '', str(value or '').strip().lower())

        def _same_addon(first, second):
            first_provider = _normalize(first.provider)
            second_provider = _normalize(second.provider)
            same_provider = bool(first_provider and first_provider == second_provider)

            first_id = _normalize(first.id)
            second_id = _normalize(second.id)
            first_name = _normalize(first.name)
            second_name = _normalize(second.name)
            first_author = _normalize(first.author)
            second_author = _normalize(second.author)

            # Provider IDs are only comparable inside that provider
            if same_provider and first_id and first_id == second_id:
                return True

            if not first_name or first_name != second_name:
                return False

            # Matching names are fine when one result lacks author metadata, but only from the same provider
            if same_provider:
                return bool(not first_author or not second_author or first_author == second_author)

            # Exact project IDs can identify the same project across providers
            if first_id and second_id and first_id == second_id:
                return True

            # Otherwise, require matching non-empty authors
            return bool(first_author and second_author and first_author == second_author)

        def _get_weight(addon):
            addon_id = _normalize(addon.id)
            addon_name = _normalize(addon.name)
            addon_author = _normalize(addon.author)

            if isinstance(query, str):
                search = _normalize(query)
                if search in [addon_id, addon_name]: return 100

                return max(
                    SequenceMatcher(None, search, addon_id).ratio(),
                    SequenceMatcher(None, search, addon_name).ratio()
                )

            if getattr(query, 'addon_object_type', None) == 'file':
                query_id = _normalize(query.id)
                query_name = _normalize(query.name)
                query_author = _normalize(query.author)
                query_file = _normalize(os.path.splitext(os.path.basename(query.path))[0])

                # Manifest IDs remain the strongest exact identity
                if query_id and query_id in [addon_id, addon_name]:
                    return 100

                # Filename is the next strongest exact identity
                if query_file and query_file in [addon_id, addon_name]:
                    return 50

                id_score = max(
                    SequenceMatcher(None, query_id, addon_id).ratio(),
                    SequenceMatcher(None, query_id, addon_name).ratio()
                )

                name_score = max(
                    SequenceMatcher(None, query_name, addon_name).ratio(),
                    SequenceMatcher(None, query_name, addon_id).ratio()
                )

                author_score = SequenceMatcher(None, query_author, addon_author).ratio() if query_author and addon_author else 0
                return (id_score * 4) + (name_score * 3) + author_score

            return 0

        def _get_newest(addons):
            resolved = [addon for addon in addons if addon.download_url]
            unresolved = [addon for addon in addons if not addon.download_url]

            def resolve(addon):
                provider = self._providers.get(addon.provider)
                return provider.get_addon_url(deepcopy(addon)) if provider else None

            if unresolved:
                with ThreadPoolExecutor(max_workers=len(unresolved)) as pool:
                    resolved.extend([
                        addon for addon in pool.map(resolve, unresolved)
                        if addon and addon.download_url
                    ])

            if not resolved:
                return addons[0]

            # Prefer an exact Minecraft-version match
            compatible = [addon for addon in resolved if addon.supported == 'yes'] or resolved

            def version(addon):
                try: return tuple(map(int, str(addon.addon_version).split('.')))
                except: return ()

            # Stable sorting preserves provider order when versions are equal
            return sorted(compatible, key=version, reverse=True)[0]

        # Return one result for lookups and updates
        if single:
            best_match = sorted(addon_list, key=_get_weight, reverse=True)[0]
            matches = [addon for addon in addon_list if _same_addon(best_match, addon)]
            return _get_newest(matches)

        # Collapse equivalent search results without combining their objects
        addon_groups = []

        for addon in addon_list:
            group = next((group for group in addon_groups if _same_addon(group[0], addon)), None)

            if group: group.append(addon)
            else:     addon_groups.append([addon])

        filtered = [_get_newest(group) if len(group) > 1 else group[0] for group in addon_groups]

        if query: filtered = sorted(filtered, key=_get_weight, reverse=True)
        return filtered

    # Adds an AddonObject to the pending queue
    def add_addon(self, addon: AddonObject):
        if not addon:
            return None

        # Normalize Telepath objects into native AddonObjects
        if not isinstance(addon, AddonObject):
            if not isinstance(addon, dict):
                return None

            addon_data = {
                key: value
                for key, value in addon.items()
                if key not in [
                    '_telepath_data',
                    '__reconstruct__'
                ]
            }

            if addon_data.get('addon_object_type') == 'web':
                addon = AddonWebObject(addon_data)

            elif addon_data.get('addon_object_type') == 'file':
                addon = AddonFileObject(addon_data)

            else:
                return None

        for queued_addon in self.addon_queue:
            if queued_addon == addon:
                return queued_addon

        self.addon_queue.append(addon)
        return addon

    # Removes an AddonObject from the pending queue
    def remove_addon(self, addon: AddonObject):
        if not addon:
            return False

        # Normalize Telepath objects into native AddonObjects
        if not isinstance(addon, AddonObject):
            if not isinstance(addon, dict):
                return False

            addon_data = {
                k: v for k, v in addon.items()
                if k not in ['_telepath_data', '__reconstruct__']
            }

            if addon_data.get('addon_object_type') == 'web':
                addon = AddonWebObject(addon_data)
            elif addon_data.get('addon_object_type') == 'file':
                addon = AddonFileObject(addon_data)
            else:
                return False

        try:
            self.addon_queue.remove(addon)
            return True

        except ValueError:
            return False

    # Clears pending add-on operations
    def clear_queue(self):
        self.addon_queue.clear()

    # Writes the pending add-on queue to paths.tmpsvr
    def write_addons(self, progress_func=None, update=False):
        server_properties = self._refresh_config()

        # Copy the pending queue for this write operation
        all_addons = deepcopy(self.addon_queue)
        addon_count = len(all_addons)

        # Skip if there are no add-ons
        if addon_count == 0:
            return True

        log_content = [addon.name for addon in all_addons]
        self._send_log(f"writing all queued add-ons to '{paths.tmpsvr}':\n{log_content}", 'info')

        addon_folder = "plugins" if manager.parse_server_type(server_properties['type']) == 'bukkit' else 'mods'
        constants.folder_check(os.path.join(paths.tmpsvr, addon_folder))
        constants.folder_check(os.path.join(paths.tmpsvr, "disabled-" + addon_folder))
        server_changed = manager.parse_server_type(self._server['type']) != manager.parse_server_type(server_properties['type']) or self._server['version'] != server_properties['version']

        def process_addon(addon_object):
            try:

                # Download resolved web objects
                if addon_object.addon_object_type == 'web':
                    return self.download_addon(addon_object, new_server=True, write_cache=False)

                # Existing file objects are either imported or updated
                else:
                    if update:
                        downloaded = self.update_addon(addon_object, new_server=True, write_cache=False)

                        # Preserve disabled state after a successful update
                        if downloaded and not getattr(addon_object, 'enabled', True):
                            disabled_path = os.path.join(paths.tmpsvr, "disabled-" + addon_folder, os.path.basename(downloaded.path))
                            os.replace(downloaded.path, disabled_path)

                        # Preserve the original state unless migrating to another version/type
                        if not downloaded:
                            destination_folder = "disabled-" + addon_folder if server_changed or not getattr(addon_object, 'enabled', True) else addon_folder
                            copy(addon_object.path, os.path.join(paths.tmpsvr, destination_folder, os.path.basename(addon_object.path)))

                        return True

                    return self.import_addon(addon_object, new_server=True)

            except Exception as e:
                self._send_log(f"failed to load '{addon_object.name}': {constants.format_traceback(e)}", 'error')

        max_pct = 0
        hook_lock = False

        with ThreadPoolExecutor(max_workers=10) as pool:
            for x, result in enumerate(pool.map(process_addon, all_addons)):

                if x > max_pct:
                    max_pct = x

                if progress_func and x >= max_pct and not hook_lock:
                    hook_lock = True
                    percentage = round(100 * ((x + 1) / addon_count))
                    def hook(value=percentage):
                        nonlocal hook_lock
                        progress_func(value)
                        time.sleep(0.2)
                        hook_lock = False

                    constants.dTimer(0, hook).start()

        if progress_func:
            progress_func(100)

        self._send_log(f"successfully wrote all queued add-ons to '{paths.tmpsvr}'", 'info')
        return True

    # Sets addon hash to determine changes
    def _set_hash(self):
        addon_hash = ""

        for addon in sorted(self.installed_addons['enabled'], key=lambda x: x.name):
            addon_hash += addon.hash

        return addon_hash

    # Checks addon hash in running config to see if it's changed
    def _hash_changed(self):
        hash_changed = False
        server_name = self._server['name']

        if server_name in constants.server_manager.running_servers:
            hash_changed = constants.server_manager.running_servers[server_name].run_data['addon-hash'] != self._addon_hash

        return hash_changed

    # Refreshes self.installed_addons list
    def _refresh_addons(self):
        if not self._addons_supported:
            return None

        if self._new_server:
            return self.installed_addons

        self._server = dump_config(self._server['name'])
        self._set_providers()
        self._set_paths()
        self.installed_addons = enumerate_addons(self._server)
        self.geyser_support = self.check_geyser()
        self._addon_hash = self._set_hash()

    def _install_geyser(self, install=True, new_server=False):
        new_server = new_server or self._new_server
        self._refresh_config()

        # Queue Geyser for a pending creation/update
        if new_server:

            # Remove the previous/source Geyser bundle
            for addon in deepcopy(self.addon_queue):
                try:
                    if is_geyser_addon(addon) or addon.name.lower() == 'viaversion':
                        self.remove_addon(addon)
                except AttributeError:
                    pass

            # Queue the complete target bundle
            if install:
                self._send_log('queueing Geyser...', 'info')
                for addon in geyser_addons(self):
                    self.add_addon(addon)

        # Install directly to an existing server
        elif install:
            self._send_log('installing Geyser...', 'info')

            def install_addon(addon):
                return self.download_addon(addon, write_cache=False)

            with ThreadPoolExecutor(max_workers=3) as pool:
                downloaded = list(pool.map(install_addon, geyser_addons(self)))

            self._refresh_addons()

            if any(downloaded):
                load_addon_cache(True, telepath=True)

        # Uninstall directly from an existing server
        else:
            self._send_log('uninstalling Geyser...', 'info')
            for addon in self.return_single_list():
                if is_geyser_addon(addon) or addon.name.lower() == 'viaversion':
                    self.delete_addon(addon)

    # Imports addon directly from file path
    def import_addon(self, addon_path: str, new_server=False):
        self._refresh_config()
        new_server = new_server or self._new_server

        # Existing operations use the live server
        # New server/update operations use foundry.new_server_info
        server_properties = self._server
        if new_server:
            from source.core.server.foundry import new_server_info
            server_properties = new_server_info

        if server_properties['type'].lower() == 'vanilla':
            return None

        if isinstance(addon_path, AddonFileObject):
            addon = addon_path
        else:
            addon = get_addon_file(addon_path, server_properties)

        if not addon:
            return None

        self._send_log(f"importing add-on '{addon_path}'...", 'info')
        imported = import_addon(addon, server_properties, tmpsvr=new_server)

        # Only refresh installed_addons when the live server was changed
        if not new_server:
            self._refresh_addons()

        if imported: self._send_log(f"successfully imported add-on '{addon_path}'", 'info')
        else:        self._send_log(f"something went wrong importing add-on '{addon_path}'", 'error')

        return imported

    # Searches for downloadable addons, returns a list of AddonWebObjects
    def search_addons(self, query: str, *args):
        self._refresh_config()
        return self._run_providers('search_addons', query, False, *args)

    # Returns advanced addon object properties
    def get_addon_info(self, addon: AddonWebObject):
        self._refresh_config()
        return self._run_providers('get_addon_info', addon)

    # Returns every available release as AddonWebObjects
    def get_addon_versions(self, addon: AddonWebObject):
        self._refresh_config()
        return self._run_providers('get_addon_versions', addon)

    # Returns the latest available supported download link
    def get_addon_url(self, addon: AddonWebObject, compat_mode=True, force_available=False):
        self._refresh_config()

        if addon.download_url and not addon.provider:
            return addon

        return self._run_providers('get_addon_url', addon, compat_mode, force_available)

    # Returns an updated AddonWebObject for an AddonFileObject
    def get_update_url(self, addon: AddonFileObject):
        self._refresh_config()

        # Resolve managed Geyser dependencies separately
        addon_id = is_geyser_addon(addon)
        if addon_id:
            updates = geyser_addons(self, addon_id, update=True)
            if updates: return updates[0]
            return None

        return self._run_providers('get_update_url', addon, single=True)

    # Searches and returns downloadable addon
    # str or AddonFileObject --> AddonWebObject
    def find_addon(self, addon: AddonFileObject or str):
        self._refresh_config()
        return self._run_providers('find_addon', addon, single=True)

    # Filters locally installed AddonFileObjects
    def filter_addons(self, query: str, *args):
        query = query.strip().lower()
        results = []

        for addon in self.return_single_list():
            addon_name = addon.name.lower().strip() if addon.name else ''
            addon_id = addon.id.lower().strip() if addon.id else ''
            addon_author = addon.author.lower().strip() if addon.author else ''
            addon_subtitle = addon.subtitle.lower().strip() if addon.subtitle else ''
            weight = 0

            if query == addon_name or query == addon_id:
                weight = 100

            else:
                weight = constants.similarity(addon_name, query)
                weight += addon_name.count(query) * 3
                weight += addon_id.count(query) * 3
                weight += addon_author.count(query)
                weight += addon_subtitle.count(query) * 0.5

            if weight > 1:
                results.append((addon, weight))

        return [a[0] for a in sorted(results, key=lambda w: w[1], reverse=True)]

    # Downloads addon directly from the closest match of name, or from AddonWebObject
    def download_addon(self, addon: AddonWebObject or str, new_server=False, write_cache=True):
        new_server = new_server or self._new_server
        server_properties = self._refresh_config()

        if server_properties['type'].lower() == 'vanilla':
            return None

        if not addon:
            return None

        downloaded: AddonFileObject | None = None
        self._send_log(f"downloading '{addon}'...", 'info')

        # Find a named add-on across every provider
        if isinstance(addon, str):
            addon = self._run_providers('find_addon', addon, single=True)

        # Resolve a provider-specific web object
        elif not addon.download_url:
            addon = self._run_providers('get_addon_url', addon)

        if addon:
            downloaded = download_addon(addon, server_properties, tmpsvr=new_server)

        # Only refresh installed_addons when the live server was changed
        if not new_server:
            self._refresh_addons()
            if downloaded and write_cache:
                load_addon_cache(True, telepath=True)

        if downloaded: self._send_log(f"successfully downloaded add-on '{addon}'")
        else:       self._send_log(f"something went wrong downloading add-on '{addon}'", 'error')

        return downloaded

    # Updates a single AddonFileObject
    def update_addon(self, addon: AddonFileObject, new_server=False, write_cache=True, track=True, new_addon: AddonWebObject = None):
        new_server = new_server or self._new_server
        server_properties = self._refresh_config()
        downloaded_addon = None

        if not new_addon:
            if not new_server and addon.update.get('url'):
                new_addon = AddonWebObject(addon.name, addon.type, addon.author, addon.subtitle, addon.update['url'], addon.id, addon.update.get('version'))
                new_addon.download_url = addon.update['url']
            else:
                new_addon = self.get_update_url(addon)

        if not new_addon:
            return None

        addon_id = str(addon.id or addon.name).lower()
        if track and not new_server:
            with self._update_lock:
                if addon_id in self.active_updates:
                    return None
                self.active_updates.append(addon_id)
            addon.update['is_updating'] = True

        try:
            downloaded_addon = self.download_addon(new_addon, new_server=new_server, write_cache=write_cache)
            if not downloaded_addon:
                return None

            # Foundry writes into a fresh temporary server
            if new_server:
                return downloaded_addon

            def same_path(first, second):
                return os.path.normcase(os.path.abspath(first)) == os.path.normcase(os.path.abspath(second))

            old_path = addon.path
            new_path = downloaded_addon.path

            # Preserve the state of disabled add-ons
            if not getattr(addon, 'enabled', True):
                disabled_path = os.path.join(self.disabled_addon_path, os.path.basename(new_path))
                constants.folder_check(self.disabled_addon_path)

                if not same_path(new_path, disabled_path):
                    os.replace(new_path, disabled_path)

                downloaded_addon.path = disabled_path
                downloaded_addon.enabled = False
                new_path = disabled_path

            # Remove an old differently-named artifact after download succeeds
            if old_path and not same_path(old_path, new_path) and os.path.isfile(old_path):
                os.remove(old_path)

            self._refresh_addons()
            return downloaded_addon

        finally:
            if track and not new_server:
                with self._update_lock:
                    try: self.active_updates.remove(addon_id)
                    except ValueError: pass
                addon.update['is_updating'] = False

    def update_all(self):
        update_list = self.get_update_list()

        with self._update_lock:
            update_list = [addon for addon in update_list if str(addon.id or addon.name).lower() not in self.active_updates]
            update_ids = [str(addon.id or addon.name).lower() for addon in update_list]
            self.active_updates.extend(update_ids)

        for addon in update_list:
            addon.update['is_updating'] = True

        updated = []
        try:
            for addon in update_list:
                result = self.update_addon(addon, track=False)
                if result: updated.append(result)

        finally:
            with self._update_lock:
                for addon_id in update_ids:
                    try: self.active_updates.remove(addon_id)
                    except ValueError: pass

            for addon in update_list:
                addon.update['is_updating'] = False

        return updated

    # Returns a list of all AddonFileObjects that currently have an update available
    def get_update_list(self):
        return [addon for addon in self.return_single_list() if addon.update.get('url')]

    # Enables/Disables installed addons
    def addon_state(self, addon: AddonFileObject, enabled=True):
        if not self._addons_supported:
            return None

        success = addon_state(addon, self._server, enabled)
        self._refresh_addons()

        return bool(success)

    # Deletes addon
    def delete_addon(self, addon: AddonFileObject):
        self._refresh_config()

        if self._new_server:
            return self.remove_addon(addon)

        if not self._addons_supported:
            return None

        try:
            os.remove(addon.path)
            removed = True
            self._send_log(f"successfully deleted '{addon}'", 'info')

        except OSError as e:
            removed = False
            self._send_log(f"failed to delete '{addon}': {constants.format_traceback(e)}", 'error')


        # Disable managed Geyser support if part of the bundle was manually removed
        if removed and is_geyser_addon(addon):
            config_file = manager.server_config(self._server['name'])

            if config_file.get('general', 'enableGeyser').lower() == 'true':
                config_file.set('general', 'enableGeyser', 'false')
                manager.server_config(self._server['name'], config_file)


        self._refresh_addons()
        return removed

    # Retrieves AddonFileObject or AddonWebObject by name
    def get_addon(self, addon_name: str, online=False):
        name = addon_name.strip().lower()
        match_list = []

        # Search online for addons instead
        if online:
            return self.find_addon(name)

        for addon in self.return_single_list():

            if name in [addon.id.lower(), addon.name.lower()]:
                return addon

            score = round(SequenceMatcher(None, addon.id.lower(), name).ratio(), 2)
            score += round(SequenceMatcher(None, addon.name.lower(), name).ratio(), 2)
            if addon.subtitle:
                score += (round(SequenceMatcher(None, addon.subtitle.lower(), name).ratio(), 2) * 5)

            match_list.append((addon, score))

        if match_list:
            return sorted(match_list, key=lambda x: x[1], reverse=True)[0][0]

    # Checks if an update is available for installed AddonFileObjects
    def check_for_updates(self):
        if not self._addons_supported or self._new_server:
            return False

        if self._server['is_modpack']:
            return False

        addon_list = self.return_single_list()
        self._send_log('checking for updates...', 'info')
        if constants.app_online:

            def check_addon(addon):

                # Skip already-discovered or currently-installing updates
                addon_id = str(addon.id or addon.name).lower()
                if addon.update.get('url') or addon_id in self.active_updates:
                    return

                try:
                    update = self.get_update_url(addon)

                    if (
                        update
                        and addon.addon_version
                        and update.addon_version
                        and constants.check_app_version(addon.addon_version, update.addon_version, limit=3)
                    ):
                        addon.update['version'] = str(update.addon_version)
                        addon.update['url'] = update.download_url

                except Exception:
                    pass

            if addon_list:
                with ThreadPoolExecutor(max_workers=min(4, len(addon_list))) as pool:
                    list(pool.map(check_addon, addon_list))

        return bool(self.get_update_list())

    # Returns single list of all addons
    def return_single_list(self) -> list[AddonFileObject]:
        if self._new_server:
            return list(self.addon_queue)

        addon_list = list(self.installed_addons['enabled'])
        addon_list.extend(self.installed_addons['disabled'])
        return addon_list

    # Returns bool of geyser installation
    def check_geyser(self):
        if not self._addons_supported:
            return False

        # Check for geyser
        if self._server['type'] in ['spigot', 'paper', 'purpur', 'fabric', 'quilt', 'neoforge']:
            for addon in self.return_single_list():
                if 'geyser' in addon.id.lower(): return True

        return False



# --------------------------------------------- Raw Addon Functions ----------------------------------------------------

# Returns file object from addon jar file
# addon.jar --> AddonFileObject
def get_addon_file(addon_path: str, server_properties, enabled=False):
    jar_name = os.path.basename(addon_path)
    addon_name = None
    addon_author = None
    addon_subtitle = None
    addon_version = None
    addon_loaders = []
    addon_type = None
    addon_id = None
    cached = False


    # Determine server information
    server_type = manager.parse_server_type(server_properties['type'])
    server_version = server_properties['version']

    # Get addon information
    if jar_name.endswith(".jar"):

        # First, check if plugin is cached
        hash_data = int(hashlib.md5(f'{os.path.getsize(addon_path)}/{os.path.basename(addon_path)}'.encode()).hexdigest(), 16)
        hash_data = str(hash_data)[:8]

        with addon_cache_lock:
            cached = deepcopy(addon_cache.get(hash_data))

            # Rebuild outdated cache entries
            if cached and cached.get('cache_version') != addon_cache_version:
                addon_cache.pop(hash_data, None)
                cached = False


        # Repair metadata created by older manual TOML parsing
        if cached:
            for key, value in cached.items():
                if isinstance(value, str):
                    cached[key] = re.sub(r'\s*#\s*(?:mandatory|optional)\b.*$', '', value, flags=re.IGNORECASE).strip()

            if '${file.' in str(cached.get('addon_version') or ''):
                with addon_cache_lock:
                    addon_cache.pop(hash_data, None)
                cached = False

            else:
                addon_name = cached['name']
                addon_loaders = cached['loaders']
                addon_author = cached['author']
                addon_subtitle = cached['subtitle']
                addon_id = cached['id']
                addon_version = cached['addon_version']

                if server_type in addon_loaders:
                    addon_type = server_type

                elif server_type == 'quilt' and 'fabric' in addon_loaders:
                    addon_type = 'fabric'

                elif addon_loaders:
                    addon_type = addon_loaders[0]

                else: addon_type = server_type


        # Next, fingerprint and parse add-on metadata
        if not cached:
            try:
                with ZipFile(addon_path, 'r') as jar_file:
                    addon_tmp = os.path.join(paths.temp, constants.gen_rstring(6))
                    constants.folder_check(addon_tmp)
                    file_list = jar_file.namelist()

                    if 'plugin.yml' in file_list:
                        addon_loaders.append('bukkit')

                    if 'quilt.mod.json' in file_list:
                        addon_loaders.append('quilt')

                    if 'fabric.mod.json' in file_list:
                        addon_loaders.append('fabric')

                    if 'META-INF/neoforge.mods.toml' in file_list:
                        addon_loaders.append('neoforge')

                    if 'mcmod.info' in file_list or 'META-INF/mods.toml' in file_list:
                        addon_loaders.append('forge')


                    # Load appropriate metadata for the server type
                    if server_type in addon_loaders:
                        addon_type = server_type

                    elif server_type == 'quilt' and 'fabric' in addon_loaders:
                        addon_type = 'fabric'

                    elif addon_loaders:
                        addon_type = addon_loaders[0]

                    else: addon_type = server_type


                    # Check if addon is actually a bukkit plugin
                    if addon_type == "bukkit":
                        try:
                            jar_file.extract('plugin.yml', addon_tmp)
                            with open(os.path.join(addon_tmp, 'plugin.yml'), 'r', encoding='utf-8', errors='ignore') as yml:
                                next_line_desc = False
                                for line in yml.readlines():

                                    if next_line_desc:
                                        addon_subtitle = line.replace("\"", "").strip()
                                        next_line_desc = False

                                    elif addon_author and addon_name and addon_version and addon_subtitle and addon_id:
                                        break

                                    elif line.strip().startswith("name:"):
                                        addon_name = line.split("name:")[1].replace("\"", "").strip()

                                    elif line.strip().startswith("author:"):
                                        addon_author = line.split("author:")[1].replace("\"", "").strip()

                                    elif line.strip().startswith("main:"):
                                        if not addon_author:
                                            if "com" in line:
                                                try: addon_author = line.split("com.")[1].split(".")[0].replace("\"", "").strip()
                                                except IndexError: addon_author = line.split(".")[1].replace("\"", "").strip()
                                            else: addon_author = line.split(".")[1].replace("\"", "").strip()
                                        try: addon_id = line.split(".")[2].replace("\"", "").strip().lower()
                                        except IndexError:
                                            if line.startswith("main:"): addon_id = line.split(".")[0].split(":")[1].strip().lower()
                                            else:                        addon_id = addon_name.lower().replace(" ", "-")

                                    elif line.strip().startswith("description:"):
                                        addon_subtitle = line.split("description:")[1].replace("\"", "").strip()
                                        next_line_desc = addon_subtitle == ">"

                                    elif line.strip().startswith("version:"):
                                        addon_version = line.split("version:")[1].replace("\"", "").replace("-", " ").strip()
                                        if "+" in addon_version:
                                            addon_version = addon_version.split("+")[0]
                                        if ";" in addon_version:
                                            addon_version = addon_version.split(";")[0]

                        except KeyError:
                            pass


                    # Check if addon is actually a forge mod
                    elif addon_type in ["forge", "neoforge"]:

                        # Check if mcmod.info exists
                        try:
                            jar_file.extract('mcmod.info', addon_tmp)
                            with open(os.path.join(addon_tmp, 'mcmod.info'), 'r', encoding='utf-8', errors='ignore') as info:
                                for line in info.readlines():

                                    if addon_author and addon_name and addon_version and addon_subtitle and addon_id:
                                        break

                                    elif line.strip().startswith("\"name\":"):
                                        addon_name = line.split("\"name\":")[1].replace("\"", "").replace(",", "").strip()

                                    elif line.strip().startswith("\"authorList\":"):
                                        addon_author = line.split("\"authorList\":")[1].replace("\"", "").replace("[", "").replace("]", "").strip()
                                        addon_author = addon_author[:-1] if addon_author.endswith(",") else addon_author
                                        addon_author = addon_author.split(',')[0].strip()

                                    elif line.strip().startswith("\"description\":"):
                                        addon_subtitle = line.split("\"description\":")[1].replace("\"", "").replace(",", "").strip()

                                    elif line.strip().startswith("\"modid\":"):
                                        addon_id = line.split("\"modid\":")[1].replace("\"", "").replace(",", "").strip().lower()

                                    elif line.strip().startswith("\"version\":"):
                                        addon_version = line.split("\"version\":")[1].replace("\"", "").replace(",", "").strip()
                                        if "+" in addon_version: addon_version = addon_version.split("+")[0]
                                        if ";" in addon_version: addon_version = addon_version.split(";")[0]

                        except KeyError:
                            pass

                        # If mcmod.info is absent, check mods.toml/neoforge.mods.toml
                        if not addon_name:
                            try:
                                try: jar_file.extract('META-INF/mods.toml', addon_tmp)
                                except: pass

                                try: jar_file.extract('META-INF/neoforge.mods.toml', addon_tmp)
                                except: pass

                                for file in glob(os.path.join(addon_tmp, 'META-INF', '*mods.toml')):

                                    # Parse a single TOML value without including inline comments
                                    def get_value(line):
                                        value = line.split('=', 1)[1].strip()
                                        if value.startswith(('"', "'")):
                                            quote = value[0]
                                            value = value[1:]
                                            end = value.find(quote)
                                            if end != -1: value = value[:end]

                                        else: value = value.split('#', 1)[0]
                                        return value.strip()


                                    with open(file, 'r', encoding='utf-8', errors='ignore') as toml:
                                        file_contents = toml.read().split("[[dependencies")[0].replace(' = ', '=')

                                        for line in file_contents.splitlines():
                                            line = line.strip()

                                            if addon_author and addon_name and addon_version and addon_subtitle and addon_id:
                                                break

                                            elif line.startswith("displayName="):
                                                addon_name = get_value(line)

                                            elif line.startswith("modId="):
                                                addon_id = get_value(line).lower()

                                            elif line.startswith("authors="):
                                                addon_author = get_value(line).split(',')[0].strip()

                                            elif line.startswith("version="):
                                                addon_version = get_value(line)

                                                # Placeholder for Implementation-Version
                                                if addon_version == "${file.jarVersion}":
                                                    try:
                                                        manifest = jar_file.read('META-INF/MANIFEST.MF').decode('utf-8', errors='ignore')

                                                        addon_version = next(
                                                            (
                                                                line.split(':', 1)[1].strip()
                                                                for line in manifest.splitlines()
                                                                if line.lower().startswith('implementation-version:')
                                                            ),
                                                            None
                                                        )

                                                    except KeyError:
                                                        addon_version = None

                                                if addon_version:
                                                    addon_version = addon_version.replace("-", " ")

                                                    if "+" in addon_version:
                                                        addon_version = addon_version.split("+")[0]

                                                    if ";" in addon_version:
                                                        addon_version = addon_version.split(";")[0]


                                        try:
                                            description = file_contents.split("description=", 1)[1]

                                            if description:
                                                addon_subtitle = description.replace("'''", "").replace("\n", " ").strip().replace("- ", " ")

                                        except IndexError:
                                            pass

                                        break

                            except KeyError:
                                pass


                    # Check if addon is actually a fabric mod
                    elif addon_type in ["fabric", "quilt"]:
                        try:
                            try:
                                file_path = os.path.join(addon_tmp, 'quilt.mod.json')
                                jar_file.extract('quilt.mod.json', addon_tmp)
                            except:
                                pass

                            try:
                                if not os.path.isfile(file_path):
                                    file_path = os.path.join(addon_tmp, 'fabric.mod.json')
                                    jar_file.extract('fabric.mod.json', addon_tmp)
                            except:
                                pass

                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as mod:
                                file_contents = json.loads(mod.read(), strict=False)

                                # Quilt mods
                                if 'quilt_loader' in file_contents:
                                    addon_type = 'quilt'
                                    data = file_contents['quilt_loader']

                                    if data['metadata']['name']:
                                        addon_name = data['metadata']['name'].strip()

                                    if data['id']:
                                        addon_id = data['id'].strip()

                                    if data['metadata']['contributors']:
                                        addon_author = list(data['metadata']['contributors'].keys())[0].strip()

                                    if data['version']:
                                        addon_version = data['version'].replace("\"", "").replace("-", " ").strip()
                                        if "+" in addon_version: addon_version = addon_version.split("+")[0].strip()
                                        if ";" in addon_version: addon_version = addon_version.split(";")[0].strip()

                                    if data['metadata']['description']:
                                        addon_subtitle = data['metadata']['description'].replace("- ", " ").strip()


                                # Fabric mods
                                else:
                                    addon_type = 'fabric'

                                    if file_contents['name']:
                                        addon_name = file_contents['name'].strip()

                                    if file_contents['id']:
                                        addon_id = file_contents['id'].strip()

                                    if file_contents['authors']:
                                        author = file_contents['authors'][0]
                                        if isinstance(author, dict): author = author.get('name')
                                        if author: addon_author = str(author).strip()

                                    if file_contents['version']:
                                        addon_version = file_contents['version'].replace("\"", "").replace("-", " ").strip()
                                        if "+" in addon_version: addon_version = addon_version.split("+")[0].strip()
                                        if ";" in addon_version: addon_version = addon_version.split(";")[0].strip()

                                    if file_contents['description']:
                                        addon_subtitle = file_contents['description'].replace("- ", " ").strip()

                        except KeyError:
                            pass


                    constants.safe_delete(addon_tmp)

            # If there's an issue with de-compilation
            except Exception as e:
                send_log('get_addon_file', f"error decompiling '{addon_path}': {constants.format_traceback(e)}")

                if not addon_version:
                    addon_version = None

                if not addon_subtitle:
                    addon_subtitle = None

                if not addon_author:
                    addon_author = None


            # Attempt to parse proper addon versions from a potential list
            addon_versions = []
            try: addon_versions = re.findall(r'(\d+[\.\d+]+)', addon_version)
            except:
                try:
                    a = addon_version.replace('_', ' ').replace('-', ' ')
                    addon_versions = re.sub(r'([^0-9.\s]+)', '', a).split(' ')
                except: pass

            # Find the most likely version from regex matches
            if addon_versions:
                if server_version in addon_versions and len(addon_versions) > 1: addon_versions.remove(server_version)
                addon_version = addon_versions[0]

            if not addon_name:

                new_name = jar_name.split(".jar")[0]
                if "- Copy" in new_name:
                    new_name = new_name.split("- Copy")[0]
                new_name = new_name.replace("-", " ")

                if " mod" in new_name or " Mod" in new_name:
                    new_name = new_name.split(" mod")[0].split(" Mod")[0]
                if " bukkit" in new_name or " Bukkit" in new_name:
                    new_name = new_name.split(" bukkit")[0].split(" Bukkit")[0]

                addon_name = new_name

                # Use server type for unknown add-ons
                if not addon_type:
                    addon_type = server_type


        if not addon_id:
            addon_id = constants.sanitize_name(addon_name.strip().lower().split(' ',1)[0], True)

        AddonObj = AddonFileObject(addon_name, addon_type, addon_author, addon_subtitle, addon_path, addon_id, addon_version)
        AddonObj.enabled = enabled
        AddonObj.loaders = addon_loaders

        # Create addon cache
        if not cached:
            cache_data = {
                'cache_version': addon_cache_version,
                'name': addon_name,
                'loaders': addon_loaders,
                'author': addon_author,
                'subtitle': addon_subtitle,
                'id': addon_id,
                'addon_version': addon_version
            }

            with addon_cache_lock:
                cached = addon_cache.setdefault(AddonObj.hash, cache_data)

            # Another thread may have inserted metadata
            AddonObj.addon_version = cached.get('addon_version')

        return AddonObj

    else: return None


# Returns True if an add-on is compatible with the server type
def check_compatibility(addon: AddonFileObject, server_properties):
    if not addon:
        return True

    server_type = manager.parse_server_type(server_properties['type'])
    addon_loaders = [
        manager.parse_server_type(loader)
        for loader in getattr(addon, 'loaders', [])
    ]

    # Fall back for older/unknown objects
    if not addon_loaders and addon.type:
        addon_loaders = [manager.parse_server_type(addon.type)]

    if server_type == 'quilt' and 'fabric' in addon_loaders:
        return True

    return not addon_loaders or server_type in addon_loaders


# Imports addon to server
# addon.jar --> AddonFileObject
def import_addon(addon_path: AddonFileObject or str, server_properties, tmpsvr=False):
    try: jar_name = os.path.basename(addon_path.path if isinstance(addon_path, AddonFileObject) else addon_path)
    except (TypeError, AttributeError):
        return None

    send_log('import_addon', f"importing '{addon_path}' to '{server_properties['name']}'...\n{f'tmpsvr: True' if tmpsvr else ''}".strip(), 'info')

    addon_folder = (
        "plugins"
        if manager.parse_server_type(server_properties['type']) == 'bukkit'
        else 'mods'
    )

    destination_path = (
        os.path.join(paths.tmpsvr, addon_folder)
        if tmpsvr
        else os.path.join(manager.server_path(server_properties['name']), addon_folder)
    )

    # Make sure the addon_path and destination_path are not the same
    try:
        if not jar_name.endswith(".jar"):
            return None

        # Convert addon_path into AddonFileObject
        if isinstance(addon_path, AddonFileObject):
            addon = addon_path
        else:
            addon = get_addon_file(addon_path, server_properties)

        if not addon:
            return None

        constants.folder_check(destination_path)
        file_name = constants.sanitize_name(addon.name, True) + ".jar"
        final_path = os.path.join(destination_path, file_name)
        source_path = os.path.abspath(addon.path)
        destination_file = os.path.abspath(final_path)

        # Do not try to copy a file over itself
        if os.path.normcase(source_path) == os.path.normcase(destination_file):
            copied = os.path.isfile(final_path)

        else:
            copied = constants.copy_to(addon.path, destination_path, file_name, overwrite=True)

        if copied and os.path.isfile(final_path):
            imported = get_addon_file(final_path, server_properties, enabled=True)
            if imported:
                send_log('import_addon', f"successfully imported '{addon_path}' to '{server_properties['name']}'")
                return imported

    except Exception as e:
        send_log('import_addon', f"failed to import '{addon_path}' to '{server_properties['name']}': {constants.format_traceback(e)}", 'error')

    return None


# Download web object into a jar file
# AddonWebObject --> AddonFileObject
def download_addon(addon: AddonWebObject, server_properties, tmpsvr=False):

    # Skip download if URL does not exist
    if not addon.download_url:
        return None

    addon_folder = "plugins" if manager.parse_server_type(server_properties['type']) == 'bukkit' else 'mods'
    destination_path = os.path.join(paths.tmpsvr, addon_folder) if tmpsvr else os.path.join(manager.server_path(server_properties['name']), addon_folder)

    file_name = constants.sanitize_name(addon.name if len(addon.name) < 35 else ' '.join(addon.name.split(' ')[:2]), True) + ".jar"
    total_path = os.path.join(destination_path, file_name)

    download_folder = os.path.join(paths.temp, f"addon-download-{constants.gen_rstring(8)}")
    download_path = os.path.join(download_folder, file_name)
    downloaded = None

    send_log('download_addon', f"downloading '{addon}' to '{destination_path}'...", 'info')

    try:
        constants.folder_check(download_folder)

        try: constants.cs_download_url(addon.download_url, file_name, download_folder)
        except requests.exceptions.SSLError:
            constants.download_url(addon.download_url, file_name, download_folder)

        # Check if addon is contained in a .zip file
        with ZipFile(download_path, 'r') as jar_file:
            nested_jar = next((f for f in jar_file.namelist() if "/" not in f and f.endswith(".jar")), None)

            if nested_jar:
                extract_folder = os.path.join(download_folder, "extract")
                constants.folder_check(extract_folder)
                jar_file.extract(nested_jar, extract_folder)
                download_path = os.path.join(extract_folder, nested_jar)

        # Validate the downloaded artifact before replacing anything
        if not get_addon_file(download_path, server_properties, enabled=True):
            raise ValueError("downloaded add-on could not be parsed")

        constants.folder_check(destination_path)
        os.replace(download_path, total_path)

        downloaded = get_addon_file(total_path, server_properties, enabled=True)
        if not downloaded: raise ValueError("installed add-on could not be parsed")

        # Provider metadata should be authoritative for downloads
        with addon_cache_lock:
            for attr in ['name', 'id', 'author', 'addon_version']:
                value = getattr(addon, attr, None)

                if value:
                    setattr(downloaded, attr, value)
                    addon_cache[downloaded.hash][attr] = value

    except Exception as e: send_log('download_addon', f"error downloading '{addon}' to '{destination_path}': {constants.format_traceback(e)}", 'error')
    else: send_log('download_addon', f"successfully downloaded '{addon}' to '{destination_path}'", 'info')
    finally: constants.safe_delete(download_folder)

    return downloaded



# ------------------------------------------ Addon List Functions ------------------------------------------------------

# Creates a dictionary of enabled and disabled addons
# dict = {
#   'enabled': [AddonFileObject1, AddonFileObject2],
#   'disabled': [AddonFileObject3, AddonFileObject4]
# }
def enumerate_addons(server_properties, single_list=False):
    if server_properties['type'].lower() == 'vanilla':
        return [] if single_list else {'enabled': [], 'disabled': []}

    # Define folder paths based on server info
    addon_folder = "plugins" if manager.parse_server_type(server_properties['type']) == 'bukkit' else 'mods'
    disabled_addon_folder = str("disabled-" + addon_folder)
    addon_folder = manager.server_path(server_properties['name'], addon_folder)
    disabled_addon_folder = manager.server_path(server_properties['name'], disabled_addon_folder)

    enabled_addons = []
    disabled_addons = []

    # Get list of enabled AddonFileObjects
    if addon_folder:
        with ThreadPoolExecutor(max_workers=15) as pool:
            def enabled(addon, *a):
                addon = get_addon_file(addon, server_properties, enabled=True)
                if addon:
                    enabled_addons.append(addon)
            pool.map(enabled, glob(os.path.join(addon_folder, "*")))
        enabled_addons = list(filter(lambda item: item is not None, enabled_addons))

    if disabled_addon_folder:
        with ThreadPoolExecutor(max_workers=15) as pool:
            def disabled(addon, *a):
                addon = get_addon_file(addon, server_properties, enabled=False)
                if addon:
                    disabled_addons.append(addon)
            pool.map(disabled, glob(os.path.join(disabled_addon_folder, "*")))

    if enabled_addons or disabled_addons:
        log_message = f"generated add-on list:"
        if enabled_addons:  log_message += f'\nenabled: {enabled_addons}'
        if disabled_addons: log_message += f'\ndisabled: {disabled_addons}'
        send_log('enumerate_addons', log_message)


    if single_list:
        new_list = constants.deepcopy(enabled_addons)
        new_list.extend(constants.deepcopy(disabled_addons))
        return new_list

    else:
        return {'enabled': enabled_addons, 'disabled': disabled_addons}



# Toggles addon state, alternate between normal and disabled folder
# AddonFileObject
def addon_state(addon: AddonFileObject, server_properties, enabled=True):
    log_prefix = 'en' if enabled else 'dis'
    server_name = server_properties['name']

    # Define folder paths based on server info
    addon_folder = "plugins" if manager.parse_server_type(server_properties['type']) == 'bukkit' else 'mods'
    disabled_addon_folder = str("disabled-" + addon_folder)
    addon_folder = os.path.join(manager.server_path(server_properties['name']), addon_folder)
    disabled_addon_folder = os.path.join(manager.server_path(server_properties['name']), disabled_addon_folder)

    addon_path, addon_name = os.path.split(addon.path)


    # Enable addon if it's disabled
    if enabled and (addon_path == disabled_addon_folder):
        constants.folder_check(addon_folder)
        new_path = os.path.join(addon_folder, addon_name)

        try:
            if os.path.exists(new_path): os.remove(new_path)
            os.rename(addon.path, new_path)

        except PermissionError as e:
            send_log('addon_state', f"'{server_name}': error {log_prefix}abling {addon}: {constants.format_traceback(e)}", 'error')
            return False

        addon.path = new_path

    # Disable addon if it's enabled
    elif not enabled and (addon_path == addon_folder):
        constants.folder_check(disabled_addon_folder)
        new_path = os.path.join(disabled_addon_folder, addon_name)

        try:
            if os.path.exists(new_path): os.remove(new_path)
            os.rename(addon.path, new_path)

        except PermissionError as e:
            send_log('addon_state', f"'{server_name}': error {log_prefix}abling {addon}: {constants.format_traceback(e)}", 'error')
            return False

        addon.path = new_path


    send_log('addon_state', f"'{server_name}': successfully {log_prefix}abled {addon}", 'info')
    return addon



# ---------------------------------------- Extraneous Addon Functions --------------------------------------------------

# name --> version, path
def dump_config(server_name: str, new_server=False):

    server_dict = {
        'name': server_name,
        'version': None,
        'type': None,
        'path': paths.tmpsvr if new_server else os.path.join(paths.servers, server_name),
        'is_modpack': False
    }


    # Pull information from new_server_info before files exist
    if new_server:
        from source.core.server.foundry import new_server_info

        server_dict['version'] = new_server_info['version']
        server_dict['type'] = new_server_info['type'].lower()
        try: server_dict['is_modpack'] = new_server_info['is_modpack']
        except: pass


    # Check auto-mcs.ini for info
    else:
        config_file = manager.server_path(server_name, constants.server_ini)
        if config_file and os.path.isfile(config_file):
            server_config = manager.server_config(server_name)

            # Only pickup server as valid with good config
            if server_name == server_config.get("general", "serverName"):
                server_dict['version'] = server_config.get("general", "serverVersion")
                server_dict['type'] = server_config.get("general", "serverType").lower()
                try: server_dict['is_modpack'] = server_config.get("general", "isModpack").lower()
                except: pass


    return server_dict


# Returns chat reporting addon if it can be found
def disable_report_addon(addon_manager):
    server_properties = addon_manager._refresh_config()
    server_type = server_properties['type'].replace('craft', '').replace('purpur', 'paper')
    addon = None

    if manager.parse_server_type(server_type) == 'bukkit':
        results = addon_manager.search_addons('freedomchat')
        addon = next((addon for addon in results if str(addon.id or '').lower() == 'freedomchat'), None)

    elif manager.parse_server_type(server_type) != 'quilt':
        results = addon_manager.search_addons('No Chat Reports')
        addon = results[0] if results else None

    if addon:
        addon = addon_manager.get_addon_url(addon, compat_mode=True, force_available=True)

    return addon


# Returns Fabric API if it can be found
def fabric_api_addon(addon_manager):
    if addon_manager._refresh_config()['type'] == 'fabric':
        return addon_manager.find_addon('Fabric API')


# Returns list of AddonWebObjects for Geyser
def geyser_addons(addon_manager, addon_id=None, update=False):
    server_properties = addon_manager._refresh_config()
    addon_id = str(addon_id or '').lower()
    final_list = []

    def _get_addon(name):
        return addon_manager._run_providers('get_update_url', name, single=True)

    # Make AddonWebObjects for dependencies
    if server_properties['type'] in ['spigot', 'paper', 'purpur']:

        # Geyser bukkit
        if not addon_id or addon_id == 'geyser':
            api_url = 'https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest'
            url = f'{api_url}/downloads/spigot'
            version = requests.get(api_url).json().get('version')
            addon = AddonWebObject('Geyser', 'bukkit', 'GeyserMC', 'Bedrock packet compatibility layer', url, 'geyser', version)
            addon.download_url = url
            final_list.append(addon)

        # Floodgate bukkit
        if not addon_id or addon_id == 'floodgate':
            api_url = 'https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest'
            url = f'{api_url}/downloads/spigot'
            version = requests.get(api_url).json().get('version')
            addon = AddonWebObject('Floodgate', 'bukkit', 'GeyserMC', 'Bedrock account compatibility layer', url, 'floodgate', version)
            addon.download_url = url
            final_list.append(addon)

        # ViaVersion bukkit
        if not addon_id or addon_id == 'viaversion':
            addon = _get_addon('ViaVersion')
            if addon: final_list.append(addon)


    elif server_properties['type'] in ['fabric', 'quilt', 'neoforge']:

        # Geyser
        if not addon_id or addon_id == 'geyser':

            # Updates are unsupported on older Fabric versions
            if not (update and server_properties['type'] == 'fabric' and constants.version_check(server_properties['version'], '<', '1.21')):
                addon = _get_addon('Geyser')
                if addon: final_list.append(addon)

        # Floodgate
        if not addon_id or addon_id == 'floodgate':
            addon = _get_addon('Floodgate')
            if addon: final_list.append(addon)

        # ViaVersion
        if not addon_id or addon_id == 'viaversion':
            addon = _get_addon('ViaVersion')
            if addon: final_list.append(addon)

    return final_list

# Return if addon is a Geyser addon
# Returns canonical ID if addon is a managed Geyser dependency
def is_geyser_addon(addon):
    addon_id = re.sub(r'[^a-z0-9]+', '', str(addon.id or '').lower())
    addon_name = re.sub(r'[^a-z0-9]+', '', str(addon.name or '').lower())

    for geyser_id in ['geyser', 'floodgate', 'viaversion']:
        if addon_id == geyser_id or addon_name.startswith(geyser_id):
            return geyser_id

    return None



# Returns list of modpack objects according to search
# Query --> ModpackWebObject
def search_modpacks(query: str, _log: bool = True, *a):
    return modpack_provider.search_modpacks(query, _log, *a)

# Returns advanced addon object properties
# ModpackWebObject
def get_modpack_info(modpack: ModpackWebObject, *a):
    return modpack_provider.get_modpack_info(modpack, *a)

# Return the latest available supported download link
# ModpackWebObject
def get_modpack_url(modpack: ModpackWebObject, *a):
    return modpack_provider.get_modpack_url(modpack, *a)

# Returns every available modpack release
def get_modpack_versions(modpack: ModpackWebObject, *a):
    return modpack_provider.get_modpack_versions(modpack, *a)

# Checks for available modpack updates
def check_modpack_updates(name: str):
    return modpack_provider.check_for_updates(name)

# Downloads a modpack archive from the current provider
def download_modpack(name: str, url: str, progress_func=None):
    return modpack_provider.download_modpack(name, url, progress_func)



# ---------------------------------------------- Usage Examples --------------------------------------------------------

# properties = {"name": "Booger Squad", "type": "spigot", "version": "1.19"}

# # Search addon:
# try:
#     addon_search = search_addons("worldedit", properties)
#     addon_search[0] = get_addon_info(addon_search[0], properties)
#     addon_search[0] = get_addon_url(addon_search[0], properties, compat_mode=True)
#     success = download_addon(addon_search[0], os.path.split(jar_path)[0])
#     print(vars(addon_search[0]))
#
# except ConnectionRefusedError:
#     print("Cloudscraper failed")



# # Update addon: pass in (jar_path, server_properties, new_version)
# jar_path = r"C:\Users\...\WorldEdit.jar"
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



# # Import addon:
# source_jar = r"C:\Users\...\worldedit - Copy (24).jar"
# import_addon(source_jar, properties)



# # Enumerate addons:
# addon_state(enumerate_addons(properties)['disabled'][0], properties, enabled=True)
# print([item.name for item in enumerate_addons(properties)['enabled']], [item.name for item in enumerate_addons(properties)['disabled']])
