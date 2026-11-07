from difflib import SequenceMatcher
from urllib.parse import urlsplit
from collections import Counter
from copy import deepcopy
from math import exp, log
import requests
import time
import json
import os
import re

from source.core import constants


# --------------------------------------------- Global Search Functions ------------------------------------------------

# Log wrapper
def send_log(object_data, message, level=None):
    from source.core import logger
    return logger.send_log(f'{__name__}.{object_data}', message, level, 'core')


# Generates content for all global searches
class SearchManager():

    stop_words = frozenset(
        "the be to of and a in that have it for not on with you do at this but by from we or an will my what so if "
        "about who get which go me when make can how is are i does using use your our where why please help guide guides "
        "t he as his they say her she one all would there their up out like time no just him know take people into year "
        "good some could them see other than then now look only come its over think also back after two work first well "
        "way even new want because any these give day most us".split()
    )

    aliases = {
        "mods": "addon", "mod": "addon", "plugins": "addon", "plugin": "addon", "addons": "addon",
        "modding": "addon", "modded": "addon",
        "downloading": "download", "downloaded": "download", "downloads": "download",
        "forwarding": "forward", "forwarded": "forward", "configuration": "config",
        "importing": "import", "imported": "import", "imports": "import",
        "installing": "install", "installed": "install", "installation": "install",
        "installations": "install", "updating": "update", "updated": "update",
        "ram": "memory", "folder": "directory", "folders": "directory", "path": "directory",
        "modpacks": "modpack", "addonpack": "modpack", "backups": "backup",
        "cloning": "clone", "cloned": "clone", "crashes": "crash",
        "joining": "join", "connected": "connect", "connection": "connect",
        "crashed": "crash", "crashing": "crash",
        "debugging": "debug", "debugged": "debug", "debugger": "debug",
        "errors": "error", "failed": "fail", "failing": "fail", "failure": "fail",
        "started": "start", "starting": "start", "stopped": "stop", "stopping": "stop",
        "connecting": "connect", "connections": "connect", "disconnected": "disconnect",
        "servers": "server", "logs": "log", "reports": "report", "commands": "command",
        "scripts": "script", "files": "file", "networks": "network", "problems": "problem"
    }

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

    def get_server_list(self):
        if constants.server_manager.menu_view_list:
            return {s._view_name: s._telepath_data for s in constants.server_manager.menu_view_list}
        else:
            return {s: None for s in constants.server_manager.create_server_list()}

    def __init__(self):

        # Used to contain attributes of pages
        class ScreenObject():
            def __init__(self, name: str, screen_id: str, options: list or staticmethod, helper_keywords=[], result_keywords={}):
                self.id = screen_id
                self.name = name
                self.options = options
                self.helper_keywords = helper_keywords
                self.result_keywords = result_keywords
                self.score = 0

        self.guide_tree = {}
        self._guide_index_source = None
        self._guide_index_data = None

        self.options_tree = {

            'MainMenu': [
                ScreenObject(
                    'Home', 'MainMenuScreen',
                    {
                        'Create a new server': 'CreateServerModeScreen',
                        'Import a server': 'ServerImportScreen',
                        'Install a modpack': 'ServerImportModpackScreen',
                        'Create from a template': 'CreateServerTemplateScreen'
                    },
                    ['addonpack', 'modpack', 'import modpack', 'import', 'create', 'new', 'instant', 'template'],
                    {
                        'Create a new server': ['make server', 'new server', 'setup'],
                        'Import a server': ['existing server', 'server folder', 'backup'],
                        'Install a modpack': ['modpack', 'modrinth', 'curseforge'],
                        'Create from a template': ['instant', 'template']
                    }
                ),
                ScreenObject('Server Manager', 'ServerManagerScreen', self.get_server_list),
                ScreenObject(
                    'Settings', 'AppSettingsScreen',
                    {
                        'Update auto-mcs': None,
                        'View changelog': f'{constants.project_repo}/releases/latest',
                        'Change language': 'ChangeLocaleScreen',
                        'Telepath': 'TelepathManagerScreen'
                    },
                    ['telepath', 'locale', 'language', 'move app', 'discord', 'reset', 'audio', 'volume', 'sound'],
                    {
                        'Update auto-mcs': ['upgrade', 'latest version', 'new version'],
                        'View changelog': ['release notes', 'changes'],
                        'Change language': ['locale', 'translation', 'translations'],
                        'Telepath': ['remote', 'pair', 'pairing', 'host']
                    }
                ),
            ],

            'CreateServer': [
                ScreenObject('Create Server (Step 1)', 'CreateServerNameScreen', {'Server Name': None}),
                ScreenObject(
                    'Create Server (Step 2)', 'CreateServerTypeScreen',
                    {
                        'Select Vanilla': None,
                        'Select Paper': None,
                        'Select Purpur': None,
                        'Select Fabric': None,
                        'Select CraftBukkit': None,
                        'Select Forge': None,
                        'Select Spigot': None
                    }
                ),
                ScreenObject('Create Server (Step 3)', 'CreateServerVersionScreen', {'Type in version': None}),
                ScreenObject(
                    'Create Server (Step 4)', 'CreateServerWorldScreen',
                    {'Browse for a world': None, 'Type in seed': None, 'Select world type': None}
                ),
                ScreenObject(
                    'Create Server (Step 5)', 'CreateServerNetworkScreen',
                    {'Specify IP/port': None, 'Type in Message Of The Day': None, 'Configure Access Control': 'CreateServerAclScreen'},
                    [],
                    {
                        'Specify IP/port': ['network', 'address', 'bind', 'port', 'lan'],
                        'Type in Message Of The Day': ['motd'],
                        'Configure Access Control': ['acl', 'permissions', 'operators', 'whitelist', 'bans']
                    }
                ),
                ScreenObject(
                    'Create Server (Access Control)', 'CreateServerAclScreen',
                    {'Configure bans': None, 'Configure operators': None, 'Configure the whitelist': None},
                    ['player', 'user', 'ban', 'white', 'op', 'rule', 'ip', 'acl', 'access control'],
                    {
                        'Configure bans': ['ban', 'banned', 'pardon'],
                        'Configure operators': ['op', 'operator', 'deop', 'permissions'],
                        'Configure the whitelist': ['whitelist', 'allowlist']
                    }
                ),
                ScreenObject(
                    'Create Server (Add-on Manager)', 'CreateServerAddonScreen',
                    {'Download add-ons': 'CreateServerAddonSearchScreen', 'Import add-ons': None, 'Toggle add-on state': None},
                    ['mod', 'plugin', 'addon', 'extension'],
                    {
                        'Download add-ons': ['install', 'modrinth', 'curseforge'],
                        'Import add-ons': ['local file', 'jar'],
                        'Toggle add-on state': ['enable', 'disable']
                    }
                ),
                ScreenObject(
                    'Create Server (Step 6)', 'CreateServerOptionsScreen',
                    {
                        'Change gamemode': None,
                        'Change difficulty': None,
                        'Specify maximum players': None,
                        'Enable spawn protection': None,
                        'Configure gamerules': None,
                        'Specify randomTickSpeed': None,
                        'Enable Bedrock support': None
                    },
                    [],
                    {
                        'Change gamemode': ['survival', 'creative', 'adventure', 'spectator'],
                        'Change difficulty': ['peaceful', 'easy', 'normal', 'hard'],
                        'Specify maximum players': ['max players', 'slots'],
                        'Enable spawn protection': ['spawn radius'],
                        'Configure gamerules': ['game rule'],
                        'Specify randomTickSpeed': ['random tick speed'],
                        'Enable Bedrock support': ['geyser', 'crossplay']
                    }
                ),
                ScreenObject('Create Server (Step 7)', 'CreateServerReviewScreen', {'Review & create server': None})
            ],

            'ServerImport': [
                ScreenObject(
                    'Import Server', 'ServerImportScreen',
                    {
                        'Import a server folder': None,
                        'Import an auto-mcs back-up': None,
                        'Import a Modpack': None,
                        'Download a Modpack': None
                    },
                    [],
                    {
                        'Import a server folder': ['existing server', 'folder'],
                        'Import an auto-mcs back-up': ['backup', 'amb'],
                        'Import a Modpack': ['modpack', 'server pack'],
                        'Download a Modpack': ['modpack', 'modrinth', 'curseforge']
                    }
                ),
            ],

            'Server': [
                ScreenObject(
                    'Server Manager', 'ServerViewScreen',
                    {'Launch server': None, 'Stop server': None, 'Restart server': None, 'Enter console commands': None},
                    [],
                    {
                        'Launch server': ['start', 'run'],
                        'Stop server': ['shutdown', 'close'],
                        'Restart server': ['reboot'],
                        'Enter console commands': ['console', 'terminal', 'command']
                    }
                ),
                ScreenObject(
                    'Back-up Manager', 'ServerBackupScreen',
                    {
                        'Save a back-up now': None,
                        'Restore from a back-up': None,
                        'Delete a back-up': None,
                        'Enable automatic back-ups': 'ServerBackupSettingsScreen',
                        'Specify maximum back-ups': 'ServerBackupSettingsScreen',
                        'Specify log retention': 'ServerBackupSettingsScreen',
                        'Open back-up directory': 'ServerBackupSettingsScreen',
                        'Migrate back-up directory': 'ServerBackupSettingsScreen',
                        'Clone this server': 'ServerCloneScreen'
                    },
                    ['backup', 'revert', 'snapshot', 'restore', 'save', 'clone'],
                    {
                        'Save a back-up now': ['snapshot'],
                        'Restore from a back-up': ['revert', 'rollback'],
                        'Delete a back-up': ['remove backup'],
                        'Enable automatic back-ups': ['auto backup', 'automatic backup'],
                        'Specify maximum back-ups': ['backup limit', 'retention'],
                        'Specify log retention': ['log limit'],
                        'Open back-up directory': ['backup folder'],
                        'Migrate back-up directory': ['move backup folder'],
                        'Clone this server': ['duplicate server', 'copy server']
                    }
                ),
                ScreenObject(
                    'Access Control', 'ServerAclScreen',
                    {'Configure bans': None, 'Configure operators': None, 'Configure the whitelist': None},
                    ['player', 'user', 'ban', 'white', 'op', 'rule', 'ip', 'acl', 'access control'],
                    {
                        'Configure bans': ['ban', 'banned', 'pardon'],
                        'Configure operators': ['op', 'operator', 'deop', 'permissions'],
                        'Configure the whitelist': ['whitelist', 'allowlist']
                    }
                ),
                ScreenObject(
                    'Add-on Manager', 'ServerAddonScreen',
                    {'Download add-ons': 'ServerAddonSearchScreen', 'Import add-ons': None, 'Toggle add-on state': None, 'Update add-ons': None},
                    ['mod', 'plugin', 'addon', 'extension'],
                    {
                        'Download add-ons': ['install', 'modrinth', 'curseforge'],
                        'Import add-ons': ['local file', 'jar'],
                        'Toggle add-on state': ['enable', 'disable'],
                        'Update add-ons': ['upgrade', 'new version']
                    }
                ),
                ScreenObject(
                    'Script Manager', 'ServerAmscriptScreen',
                    {
                        'Download scripts': 'ServerAmscriptSearchScreen',
                        'Import scripts': None,
                        'Create a new script': 'CreateAmscriptScreen',
                        'Edit a script': None,
                        'Open script directory': None
                    },
                    ['amscript', 'script', 'ide', 'develop'],
                    {
                        'Download scripts': ['install script', 'library'],
                        'Import scripts': ['ams file', 'local script'],
                        'Create a new script': ['write script', 'new script'],
                        'Edit a script': ['ide', 'editor'],
                        'Open script directory': ['script folder', 'files']
                    }
                ),
                ScreenObject(
                    'Server Settings', 'ServerSettingsScreen',
                    {
                        "Edit configuration files": 'ServerConfigScreen',
                        "Edit 'server.properties'": None,
                        'Open server directory': None,
                        'Specify memory usage': None,
                        'Change MOTD': None,
                        'Specify IP/port': None,
                        'Change launch flags': None,
                        'Enable proxy (playit)': None,
                        'Install proxy (playit)': None,
                        'Enable Bedrock support': None,
                        'Enable automatic updates': None,
                        'Update this server': None,
                        "Change 'server.jar'": 'MigrateServerTypeScreen',
                        'Rename this server': None,
                        'Change world file': 'ServerWorldScreen',
                        'Delete this server': None
                    },
                    ['ram', 'memory', 'server.properties', 'properties', 'rename', 'delete', 'bedrock', 'proxy', 'ngrok', 'playit', 'update', 'jvm', 'motd', 'yml', 'config'],
                    {
                        "Edit configuration files": ['config', 'yaml', 'yml', 'json', 'toml'],
                        "Edit 'server.properties'": ['properties'],
                        'Open server directory': ['folder', 'files'],
                        'Specify memory usage': ['ram', 'heap', 'xmx', 'xms'],
                        'Change MOTD': ['message of the day'],
                        'Specify IP/port': ['network', 'address', 'bind', 'port', 'lan'],
                        'Change launch flags': ['jvm', 'java arguments', 'java flags'],
                        'Enable proxy (playit)': ['tunnel', 'public address', 'public server'],
                        'Install proxy (playit)': ['tunnel', 'public address', 'public server'],
                        'Enable Bedrock support': ['geyser', 'crossplay'],
                        'Enable automatic updates': ['auto update'],
                        'Update this server': ['upgrade', 'new version'],
                        "Change 'server.jar'": ['distribution', 'server type', 'migrate'],
                        'Rename this server': ['name'],
                        'Change world file': ['level', 'map'],
                        'Delete this server': ['remove']
                    }
                )
            ]
        }

    # Reset cached guide search data when the manifest changes
    def _set_guide_tree(self, data):
        self.guide_tree = data
        self._guide_index_source = None
        self._guide_index_data = None

    # Cache the guides to a .json file
    def cache_pages(self, cancel_func=None):
        cache_file = os.path.join(constants.paths.cache, 'guide-cache.json')
        etag_file = os.path.join(constants.paths.cache, 'guide-cache.etag')
        cache_url = f'{constants.api_url}/guides/cache'
        cache_data = None

        def cancelled():
            return bool(cancel_func and cancel_func())

        def wait_delay(delay):
            end = time.monotonic() + delay
            while time.monotonic() < end:
                if cancelled(): return False
                time.sleep(min(0.1, end - time.monotonic()))
            return True

        # Load the existing cache first as a fallback
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8', errors='ignore') as f:
                    cache_data = json.load(f)

                if not isinstance(cache_data, dict) or not cache_data:
                    raise ValueError('guide cache is empty or invalid')

                self._set_guide_tree(cache_data)

            except Exception as e:
                cache_data = None
                self._send_log(f"failed to load guide cache from '{cache_file}': {constants.format_traceback(e)}", 'warning')

        # No need to refresh if the application is offline
        if not constants.app_online:
            if cache_data:
                self._send_log(f"initialized SearchManager from cache in '{cache_file}'", 'info')
                return True

            self._send_log(f"failed to fully initialize SearchManager: {constants.app_title} is offline", 'error')
            return False

        headers = {}

        if cache_data and os.path.exists(etag_file):
            try:
                with open(etag_file, 'r', encoding='utf-8', errors='ignore') as f:
                    etag = f.read().strip()
                    if etag: headers['If-None-Match'] = etag
            except: pass

        # Refresh the cache from the website API
        for attempt in range(3):
            if cancelled(): return False

            try:
                response = requests.get(cache_url, headers=headers, timeout=(5, 15))

                if response.status_code == 304 and cache_data:
                    self._send_log(f"initialized SearchManager from cache in '{cache_file}' (up to date)", 'info')
                    return True

                response.raise_for_status()
                new_data = response.json()

                if not isinstance(new_data, dict) or not new_data:
                    raise ValueError('downloaded guide cache is empty or invalid')

                if not all(isinstance(data, dict) and isinstance(data.get('content'), dict) and data.get('url') for data in new_data.values()):
                    raise ValueError('downloaded guide cache has an invalid structure')

                self._set_guide_tree(new_data)

                # Cache writes failing should not prevent this session from using the new manifest
                try:
                    constants.folder_check(constants.paths.cache)
                    temp_file = cache_file + '.tmp'

                    with open(temp_file, 'wb') as f:
                        f.write(response.content)

                    os.replace(temp_file, cache_file)
                    etag = response.headers.get('ETag')

                    if etag:
                        with open(etag_file, 'w', encoding='utf-8') as f:
                            f.write(etag)
                    elif os.path.exists(etag_file):
                        os.remove(etag_file)

                except Exception as e:
                    self._send_log(f"failed to write guide cache to '{cache_file}': {constants.format_traceback(e)}", 'warning')

                self._send_log(f"initialized SearchManager from '{cache_url}'", 'info')
                return True

            except (requests.RequestException, ValueError) as e:
                self._send_log(f"guide cache request to '{cache_url}' failed: {constants.format_traceback(e)}", 'warning')

            if attempt < 2 and not wait_delay(1):
                return False

        # A failed refresh should never destroy a previously valid cache
        if cache_data:
            self._set_guide_tree(cache_data)
            self._send_log(f"using existing guide cache after refresh failure in '{cache_file}'", 'warning')
            return True

        return False

    # Normalize text for local UI and guide searching
    def _tokens(self, value: str):
        value = value.lower().replace('auto-mcs', 'automcs')
        value = re.sub(r'\badd[\s-]?ons?\b', 'addon', value)
        value = re.sub(r'\bback[\s-]?ups?\b', 'backup', value)
        value = re.sub(r'\baddon[\s-]?packs?\b', 'modpack', value)
        words = re.findall(r'[a-z0-9]+', value)
        return [self.aliases.get(word, word) for word in words if word not in self.stop_words]

    # Remove markup and examples which should not heavily influence relevance
    def _search_text(self, value: str):
        value = re.sub(re.escape('```') + r'[\s\S]*?' + re.escape('```'), ' ', value)
        value = re.sub(r'!?\[([^\]]*)\]\(<[^>]*>\)', r'\1', value)
        return re.sub(r'[`*_#<>]', '', value)

    # Coerce common searches to the intended guide family
    def _guess_intent(self, query: str, words: list[str]):
        raw = query.lower()
        terms = set(words)
        has = lambda *names: bool(terms.intersection(names))

        if ('automcs' in terms or re.search(r'\bthis\b', raw)) and re.search(r'\bwhat\b', raw):
            return 'getting started', None
        if ('automcs' in terms or re.search(r'\bthis\b', raw)) and not has('addon', 'script', 'amscript') and (has('download', 'install', 'get') or re.search(r'\buse\b', raw)):
            return 'installation', None
        if has('level', 'world') and not has('backup'):
            return 'world', None
        if has('clone'):
            return 'clone', 'Server Manager'
        if has('memory'):
            return 'memory', None
        if has('ide'):
            return 'using the ide', 'amscript'
        if re.search(r'\bmodding\b', raw) or (has('addon') and has('install')):
            return 'installation addon', 'Server Manager'
        if has('distribution'):
            return 'server type', None
        if has('acl') or 'access control' in raw:
            return 'access control', 'Server Manager'
        if has('create', 'make') and has('server'):
            return 'create a server', 'Setup'
        if has('amscript') and 'what is' in raw:
            return 'amscript', 'amscript'
        if 'port forward' in raw or has('nat', 'tcp', 'udp') or 'address translation' in raw or 'port trigger' in raw:
            return 'port forwarding', 'Networking'
        if has('port', 'ip') and 'telepath' not in raw:
            return 'lan configuration', 'Networking'
        if has('amscript') and (has('download', 'install', 'get') or re.search(r'\buse\b', raw)):
            return 'installation', 'amscript'

        return '', None

    # Prevent specialized guides from winning unrelated searches
    def _allow_reference(self, query: str, words: list[str], page: dict):
        path = urlsplit(page.get('url', '')).path
        terms = set(words)

        if path.startswith('/guides/amscript/api'):
            return 'amscript' in terms or bool(re.search(r'\b[a-z_]+\.[a-z_]+\s*\(', query.lower()))
        if path == '/guides/server-manager/add-ons':
            return 'addon' in terms or bool(terms & {'modrinth', 'curseforge', 'hangar'})
        if path == '/guides/server-manager/back-ups':
            return 'backup' in terms or bool(terms & {'restore', 'clone', 'cloning'})

        return True

    # Preserve domain-specific guide search preferences
    def _intent_bonus(self, page: dict, section: str, hint, words: list[str]):
        phrase, category = hint
        title_tokens = set(self._tokens(page.get('title', '')))
        category_tokens = set(self._tokens(page.get('category', '')))
        heading_tokens = set(self._tokens(section))

        if phrase:
            goal = set(self._tokens(phrase))
            if goal and goal <= (title_tokens | category_tokens | heading_tokens):
                if not category or self._tokens(page.get('category', '')) == self._tokens(category):
                    return 12.0

        topics = set(words)
        path = urlsplit(page.get('url', '')).path

        if 'addon' in topics and path == '/guides/server-manager/add-ons':
            return 5.0
        if 'backup' in topics and path == '/guides/server-manager/back-ups':
            return 2.5
        if 'amscript' in topics and self._tokens(page.get('category', '')) == ['amscript']:
            return 1.0

        return 0.0

    # BM25 normalization used by guide and UI search
    def _bm25(self, term: str, counts: Counter, average: float):
        count = counts.get(term, 0)
        if not count: return 0.0
        length = sum(counts.values())
        k = 1.2
        return count * (k + 1) / (count + k * (0.25 + 0.75 * length / average))

    # Get the actual article name from the normalized cache
    def _guide_name(self, key: str, page: dict):
        title = page.get('title', key)
        return key if title.lower() == 'overview' else title

    # Build the guide search index once per manifest
    def _search_index(self):
        if self.guide_tree is self._guide_index_source and self._guide_index_data is not None:
            return self._guide_index_data

        documents = []
        frequencies = Counter()
        lengths = Counter()
        fields = ('category', 'title', 'heading', 'description', 'body')

        for key, page in self.guide_tree.items():
            page_title = self._guide_name(key, page)
            category = page.get('category', 'Guides')

            for section, body in page['content'].items():
                counter = {
                    'category': Counter(self._tokens(category)),
                    'title': Counter(self._tokens(page_title)),
                    'heading': Counter(self._tokens(page_title if section == 'overview' else section)),
                    'description': Counter(self._tokens(page.get('description', ''))),
                    'body': Counter(self._tokens(self._search_text(body))),
                }

                for name in fields:
                    lengths[name] += sum(counter[name].values())

                frequencies.update(set().union(*(set(c) for c in counter.values())))
                documents.append((key, page, section, counter))

        size = len(documents)
        averages = {name: max(1, lengths[name] / max(size, 1)) for name in fields}

        self._guide_index_source = self.guide_tree
        self._guide_index_data = (documents, frequencies, averages, size)
        return self._guide_index_data

    # Add the configured website URL to a route from the guide cache
    def _website_url(self, route: str):
        if route.startswith(('http://', 'https://')):
            return route
        return f'{constants.website.rstrip("/")}/{route.lstrip("/")}'

    # Convert a guide match into the existing GuideResult format
    def _guide_result(self, page: dict, key: str, section: str, score: float):
        anchor = page.get('anchors', {}).get(section, '')
        category = page.get('category')
        title = self._guide_name(key, page)
        display_title = f'{category} - {title}' if category and category != 'Guides' and self._tokens(category) != self._tokens(title) else title
        route = page['url'] + (f'#{anchor}' if anchor else '')

        return GuideResult(
            display_title,
            'View guide from auto-mcs.com',
            self._website_url(route),
            score = round(min(score, 1.0) * 100, 3)
        )

    # Search the downloaded guide manifest using the website API algorithm
    def _search_guides(self, query: str):
        words = list(dict.fromkeys(self._tokens(query)))
        if not words: return None

        phrase = ' '.join(words)
        hint = self._guess_intent(query, words)
        eligible = lambda page: self._allow_reference(query, words, page)

        # Prefer an exact article match before searching individual sections
        exact_guides = [(key, page) for key, page in self.guide_tree.items() if eligible(page) and self._tokens(self._guide_name(key, page)) == words]
        if len(exact_guides) == 1:
            key, page = exact_guides[0]
            return self._guide_result(page, key, 'overview', 1.0)

        # A category lookup should land at that category's overview
        for key, page in self.guide_tree.items():
            if eligible(page) and self._tokens(page.get('category', '')) == words and page.get('title', '').lower() == 'overview':
                return self._guide_result(page, key, 'overview', 1.0)

        # Exact article title
        exact_titles = [(key, page) for key, page in self.guide_tree.items() if eligible(page) and self._tokens(page.get('title', key)) == words]
        if len(exact_titles) == 1 and not hint[0]:
            key, page = exact_titles[0]
            return self._guide_result(page, key, 'overview', 1.0)

        documents, df, averages, size = self._search_index()
        if not size: return None

        resolved_words = {}

        for word in words:
            if word in df:
                resolved_words[word] = (word, 1.0)
                continue

            alternatives = [(term, SequenceMatcher(None, word, term).ratio()) for term in df if abs(len(term) - len(word)) <= 2]
            alternatives = [(term, ratio) for term, ratio in alternatives if ratio >= 0.85]
            resolved_words[word] = ((max(alternatives, key=lambda item: item[1])[0], 0.6) if alternatives else (word, 1.0))

        best = None
        best_score = 0.0

        for key, page, section, counters in documents:
            if not eligible(page): continue

            depth = page.get('depths', {}).get(section, 1 if section == 'overview' else 2)
            prominence = {1: 1.0, 2: 0.9, 3: 0.75, 4: 0.6}.get(depth, 0.5)
            weights = {'heading': 6.0 * prominence, 'title': 4.0, 'description': 2.0, 'category': 0.8, 'body': 0.65}
            matched = 0
            relevance = 0.0

            for word in words:
                match, match_similarity = resolved_words[word]
                if not any(match in counts for counts in counters.values()): continue

                matched += 1
                idf = log(1 + (size - df[match] + 0.5) / (df[match] + 0.5))
                term_score = sum(weight * self._bm25(match, counters[field], averages[field]) for field, weight in weights.items())
                relevance += idf * term_score * match_similarity

            if not matched: continue

            coverage = matched / len(words)
            relevance *= coverage ** 2

            heading = ' '.join(self._tokens(self._guide_name(key, page) if section == 'overview' else section))
            title = ' '.join(self._tokens(self._guide_name(key, page)))

            if heading == phrase:
                relevance += 7.0 * prominence
            elif phrase in heading and len(phrase) >= 4:
                relevance += 2.5 * prominence

            if title == phrase:
                relevance += 4.0
            if section == 'overview':
                relevance += 0.7 * coverage

            relevance += self._intent_bonus(page, section, hint, words)

            if relevance > best_score:
                best_score = relevance
                best = self._guide_result(page, key, section, 1 - exp(-relevance / 10.0))

        return best if best_score >= 0.6 else None

    # Generate a list of available options based on the current screen
    def filter_options(self, current_screen):
        from source.core.server.foundry import new_server_info
        from source.core.tools import playit

        # Copy the list instead of mutating MainMenu with extend()
        screen_list = list(self.options_tree['MainMenu'])
        final_list = []

        if current_screen.startswith('ServerImport'):
            screen_list.extend(self.options_tree['ServerImport'])

        if current_screen.startswith('CreateServer'):
            for screen in self.options_tree['CreateServer']:
                if not (new_server_info['type'] == 'vanilla' and screen.id == 'ServerAddonScreen'):
                    if screen not in screen_list:
                        screen_list.append(screen)

        if constants.server_manager.current_server:
            for screen in self.options_tree['Server']:
                if not (constants.server_manager.current_server.type == 'vanilla' and screen.id == 'ServerAddonScreen'):
                    if screen not in screen_list:
                        screen_list.append(screen)

        # Iterate through available screens, settings, and servers
        for screen in screen_list:

            if screen.id == 'ServerManagerScreen':
                if current_screen != screen.id:
                    final_list.append(ScreenResult(screen.name, 'Configuration page', screen.id, screen.helper_keywords))

                for server, telepath_data in screen.options().items():
                    if telepath_data:
                        telepath = deepcopy(telepath_data)
                        telepath['name'] = server.rsplit('/', 1)[-1]
                        keywords = [telepath['host'], telepath['nickname'], 'telepath', 'remote', telepath['name']]
                        final_list.append(ServerResult(server, 'Telepath server', None, keywords, telepath=telepath))
                    else:
                        final_list.append(ServerResult(server, 'Installed server', None))

            elif (screen.id.startswith('Server') and 'Import' not in screen.id) and constants.server_manager.current_server:
                keywords = list(screen.options.keys())
                keywords.extend(screen.helper_keywords)

                if current_screen != screen.id:
                    final_list.append(ScreenResult(screen.name, f'Configuration page ({constants.server_manager.current_server.name})', screen.id, keywords))

                for setting, value in screen.options.items():

                    # Don't show navigation to the page that's already open
                    if value and value == current_screen:
                        continue

                    # Ignore results for running server
                    if constants.server_manager.current_server.running and setting.lower() in (
                        'launch server', 'update this server', "change 'server.jar'", 'rename this server', 'change world file', 'delete this server'
                    ):
                        continue

                    elif not constants.server_manager.current_server.running and setting.lower() in ('restart server', 'stop server'):
                        continue

                    # Change results for proxy installation
                    if setting.lower() == 'enable proxy (playit)' and not playit.manager._check_agent():
                        continue
                    if setting.lower() == 'install proxy (playit)' and playit.manager._check_agent():
                        continue

                    # If server is up-to-date, hide update prompt
                    if setting.lower() == 'update this server' and not constants.server_manager.current_server.update_string:
                        continue

                    action_keywords = screen.result_keywords.get(setting, [])
                    context_keywords = [screen.name] + screen.helper_keywords

                    final_list.append(
                        SettingResult(
                            setting,
                            f'Action in {screen.name} ({constants.server_manager.current_server.name})',
                            value if value else screen.id,
                            action_keywords,
                            context_keywords=context_keywords
                        )
                    )

            else:
                keywords = list(screen.options.keys())
                keywords.extend(screen.helper_keywords)

                if current_screen != screen.id:
                    final_list.append(ScreenResult(screen.name, 'Configuration page', screen.id, keywords))

                for setting, value in screen.options.items():

                    # Don't show navigation to the page that's already open
                    if value and value == current_screen:
                        continue

                    if setting.lower() == 'update auto-mcs' and constants.app_latest:
                        continue

                    action_keywords = screen.result_keywords.get(setting, [])
                    context_keywords = [screen.name] + screen.helper_keywords

                    final_list.append(
                        SettingResult(
                            setting,
                            f'Action in {screen.name}',
                            value if value else screen.id,
                            action_keywords,
                            context_keywords=context_keywords
                        )
                    )

        return final_list

    # Score screens, actions, and servers with the same weighted search model
    def _score_options(self, objects, query, current_screen):
        words = list(dict.fromkeys(self._tokens(query)))
        if not words: return

        phrase = ' '.join(words)
        fields = ('title', 'keywords', 'context', 'subtitle')
        documents = []
        frequencies = Counter()
        lengths = Counter()

        for obj in objects:
            search_title = getattr(obj, 'search_title', obj.title)

            counters = {
                'title': Counter(self._tokens(str(search_title))),
                'keywords': Counter(word for keyword in obj.keywords for word in self._tokens(str(keyword))),
                'context': Counter(word for keyword in getattr(obj, 'context_keywords', []) for word in self._tokens(str(keyword))),
                'subtitle': Counter(self._tokens(str(obj.subtitle))),
            }

            for field in fields:
                lengths[field] += sum(counters[field].values())

            frequencies.update(set().union(*(set(c) for c in counters.values())))
            documents.append((obj, search_title, counters))

        size = len(documents)
        if not size: return

        averages = {field: max(1, lengths[field] / size) for field in fields}
        resolved_words = {}

        for word in words:
            if word in frequencies:
                resolved_words[word] = (word, 1.0)
                continue

            # Type-ahead should still rank partial words sensibly
            prefixes = [term for term in frequencies if len(word) >= 3 and term.startswith(word)]

            if prefixes:
                resolved_words[word] = (min(prefixes, key=lambda term: (len(term), term)), 0.8)
                continue

            alternatives = [(term, SequenceMatcher(None, word, term).ratio()) for term in frequencies if abs(len(term) - len(word)) <= 3]
            alternatives = [(term, ratio) for term, ratio in alternatives if ratio >= 0.82]
            resolved_words[word] = ((max(alternatives, key=lambda item: item[1])[0], 0.65) if alternatives else (word, 1.0))

        for obj, search_title, counters in documents:
            matched = 0
            relevance = 0.0
            weights = {'title': 6.0, 'keywords': 2.5, 'context': 0.7, 'subtitle': 0.5}

            for word in words:
                match, match_similarity = resolved_words[word]
                if not any(match in counts for counts in counters.values()): continue

                matched += 1
                idf = log(1 + (size - frequencies[match] + 0.5) / (frequencies[match] + 0.5))
                term_score = sum(weight * self._bm25(match, counters[field], averages[field]) for field, weight in weights.items())
                relevance += idf * term_score * match_similarity

            title = ' '.join(self._tokens(str(search_title)))
            relevance += SequenceMatcher(None, phrase, title).ratio() * 0.75

            if matched:
                coverage = matched / len(words)
                relevance *= coverage ** 2

            # Exact result title always wins its own object
            if title == phrase:
                obj.score = 100

            else:
                if phrase in title and len(phrase) >= 3:
                    relevance += 3.0

                # Explicit result tags are stronger than general context
                for keyword in obj.keywords:
                    keyword = ' '.join(self._tokens(str(keyword)))
                    if keyword == phrase:
                        relevance += 4.0
                        break

                obj.score = round((1 - exp(-relevance / 10.0)) * 100, 3)

            # Preserve the existing contextual server weighting
            if obj.type == 'server' and current_screen == 'ServerManagerScreen':
                obj.score *= 2
            elif obj.type == 'server' and (current_screen.startswith('Server') or current_screen.startswith('CreateServer')):
                obj.score /= 1.5

            # Prefer navigation/actions over guides when they lead somewhere else
            elif obj.type in ('setting', 'screen') and obj.target != current_screen:
                obj.score *= 1.15

    # Generate a list of weighted results from a search
    def execute_search(self, current_screen, query):
        self._send_log(f"searching for '{query}'...")

        match_list = {
            'guide': SearchObject(),
            'setting': [],
            'screen': [],
            'server': []
        }

        # Search screens, quick actions, and installed servers
        options_list = self.filter_options(current_screen)

        if options_list:
            self._score_options(options_list, query, current_screen)

            for obj in options_list:
                match_list[obj.type].append(obj)

        # Guide results still require the website to open
        if constants.app_online and self.guide_tree:
            guide_result = self._search_guides(query)

            if guide_result:
                match_list['guide'] = guide_result

                # Preserve the existing preference for explicit help/guide searches
                if 'guide' in query.lower() or 'help' in query.lower():
                    match_list['guide'].score = 1000

        match_list['setting'] = tuple(sorted(match_list['setting'], key=lambda x: x.score, reverse=True))
        match_list['screen'] = tuple(sorted(match_list['screen'], key=lambda x: x.score, reverse=True))
        match_list['server'] = tuple(sorted(match_list['server'], key=lambda x: x.score, reverse=True))

        self._send_log(f"results for '{query}':\n{match_list}")
        return match_list


# Base search result
class SearchObject():
    def __init__(self):
        self.type = 'undefined'
        self.score = 0

    def __repr__(self):
        title = getattr(self, 'title', None)
        return f'<{self.__class__.__name__} "{title}">'


# Search result that matches a setting
class SettingResult(SearchObject):
    def __init__(self, title, subtitle, target, keywords=[], score=0, context_keywords=[]):
        super().__init__()
        self.type = 'setting'
        self.icon = os.path.join(constants.paths.ui_assets, 'icons', 'play-circle-sharp.png')
        self.color = (0.7, 0.7, 1, 1)
        self.title = title
        self.subtitle = subtitle
        self.target = target
        self.keywords = keywords
        self.context_keywords = context_keywords
        self.score = score


# Search result that matches an online guide
class GuideResult(SearchObject):
    def __init__(self, title, subtitle, target, keywords=[], score=0):
        super().__init__()
        self.type = 'guide'
        self.icon = os.path.join(constants.paths.ui_assets, 'icons', 'newspaper.png')
        self.color = (0.6, 1, 0.75, 1)
        self.title = title
        self.subtitle = subtitle
        self.target = target
        self.keywords = keywords
        self.score = score


# Search result that matches an installed server
class ServerResult(SearchObject):
    def __init__(self, title, subtitle, target, keywords=[], score=0, telepath=None):
        super().__init__()
        self._telepath_data = telepath
        self.type = 'server'
        self.icon = os.path.join(constants.paths.ui_assets, 'icons', 'sm', 'terminal.png')
        self.color = (1, 0.598, 0.9, 1)
        self.search_title = title

        if self._telepath_data:
            self.title = f'[color=#9383A2]{self._telepath_data["display-name"]}/[/color]{self._telepath_data["name"]}'
        else:
            self.title = title

        self.subtitle = subtitle
        self.target = target
        self.keywords = keywords
        self.context_keywords = []
        self.score = score


# Search result that matches a configuration page
class ScreenResult(SearchObject):
    def __init__(self, title, subtitle, target, keywords=[], score=0):
        super().__init__()
        self.type = 'screen'
        self.icon = os.path.join(constants.paths.ui_assets, 'icons', 'exit-sharp.png')
        self.color = (0.639, 1, 1, 1)
        self.title = title
        self.subtitle = subtitle
        self.target = target
        self.keywords = keywords
        self.context_keywords = []
        self.score = score


# Global search manager
search_manager: SearchManager = None


def init_manager():
    global search_manager
    search_manager = SearchManager()
    return search_manager
