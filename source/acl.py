from concurrent.futures import ThreadPoolExecutor
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
from urllib.request import urlopen
from datetime import timedelta
from copy import deepcopy
from glob import glob
import json_repair
import threading
import ipaddress
import constants
import socket
import time
import json
import re
import os

from amscript import PlayerScriptObject


# Auto-MCS Access Control API
# ----------------------------------------------- Global Variables -----------------------------------------------------

cache_folder = constants.cacheDir
uuid_db = os.path.join(cache_folder, "uuid-db.json")
global_acl_file = os.path.join(constants.configDir, "global-acl.json")

# ------------------------------------------------- ACL Objects --------------------------------------------------------

# Used to house an ACL rule, stored in AclManager lists
class AclRule():
    def _to_json(self):
        return {k: getattr(self, k) for k in dir(self) if not (k.endswith('__') or callable(getattr(self, k)))}

    def set_scope(self, is_global=False):
        self.rule_scope = 'global' if is_global else 'local'
        return self.rule_scope

    def __init__(self, rule, acl_group, is_global=False, extra_data=None):

        # ID of the rule
        self.rule = rule

        # player, ip
        self.rule_type = "ip" if (rule.count(".") == 3) else "player"

        # local, global
        self.rule_scope = self.set_scope(is_global)

        # ops, bans, wl, subnets
        self.acl_group = acl_group

        # dict of any extra content
        if extra_data is None:
            extra_data = {}
        self.extra_data = extra_data

        # To be added when rule is displayed from AclManager
        self.display_data = None

        # To determine which view list the object is in
        self.list_enabled = True

    # This might break something, delete if it causes crashes
    def __str__(self):
        return str(self.rule)


# Instantiate class with "server_name" (case-sensitive)
# Server ACL object to house AclRules with manipulative functions
# self._new_server denotes cached ACL to be written when the server is created with self.write_rules()
class AclManager():
    def _to_json(self):
        final_data = {k: getattr(self, k) for k in dir(self) if not (k.endswith('__') or callable(getattr(self, k)))}
        final_data['list_items'] = {}
        final_data['displayed_rule'] = None
        final_data['rules'] = {k: [i._to_json() for i in v] for k, v in final_data['rules'].items()}
        return final_data

    def __init__(self, server_name: str):

        # Check if config file exists to determine new server status
        self._new_server = (not constants.server_path(server_name, constants.server_ini))

        self._server = dump_config(server_name, self._new_server)
        self.rules = self._load_acl(new_server=self._new_server)
        self.playerdata = self._get_playerdata() if not self._new_server else []

        self.list_items = self._gen_list_items()
        self.whitelist_enabled = self._server['whitelist']
        self.displayed_rule = None

    # Inherit get_uuid method
    def get_uuid(self, *args, **kwargs):
        return get_uuid(*args, **kwargs)

    # Returns the value of the requested attribute (for remote)
    def _sync_attr(self, name):
        return constants.sync_attr(self, name)

    # Scrape the server's joined users
    def _get_playerdata(self):
        server_name = self._server['name']
        version = self._server['version']
        server_path = self._server['path']
        server_world = self._server['world']

        playerdata_list = []

        # Adds AclRule to playerdata list
        def add_user(player_info):

            acl_object = AclRule(rule=player_info['name'], acl_group='cache')

            for key, value in player_info.items():
                if key != 'name':
                    acl_object.extra_data[key] = value

            playerdata_list.append(acl_object)

        # Function to process playerdata in threads
        def iter_playerdata(player):

            player_info = get_uuid(player)

            if player_info:
                add_user(player_info)

        # Function to process usercache.json file in threads
        def iter_usercache(item):

            # if usercache exists
            if usercache:

                player_info = {
                    "uuid": f"{item['uuid']}",
                    "name": f"{item['name']}"
                }

                add_user(player_info)

                if item['uuid'] in uuid_list:
                    return player_info

                else:
                    temp_folder = os.path.join(cache_folder, 'uuid-temp')
                    constants.folder_check(temp_folder)

                    with open(
                        os.path.join(temp_folder, f"uuid-{item['uuid'].lower().replace('-', '')}.json"),
                        "w"
                    ) as user_file:

                        user_file.write(json.dumps(player_info, indent=2))

            else:
                iter_playerdata(item)


        # Check cached world playerdata for old versions
        if constants.version_check(version, "<", constants.json_format_floor):
            data_path = os.path.join(server_path, server_world, 'players')

            with ThreadPoolExecutor(max_workers=15) as pool:
                pool.map(
                    iter_playerdata,
                    [os.path.basename(item).lower().split(".dat")[0] for item in glob(os.path.join(data_path, '*'))]
                )

        # Check cached world playerdata for modern versions
        else:

            # Use usercache.json and fallback on resolving world playerdata
            try:
                data_path = os.path.join(server_path, server_world, 'playerdata')
            except TypeError:
                data_path = None
            usercache = []
            fallback = False

            try:
                with open(os.path.join(server_path, 'usercache.json'), 'r') as f:
                    file = json.load(f)
                    usercache = file

            except FileNotFoundError:
                fallback = True

            if ((not usercache) or (fallback)) and data_path:
                usercache = [os.path.basename(item).lower().split(".dat")[0] for item in glob(os.path.join(data_path, '*'))]

            if usercache:
                try:
                    with open(f"{cache_folder}\\uuid-db.json", "r") as f:
                        db = json.load(f)
                        uuid_list = [x['uuid'] for x in db]
                except FileNotFoundError:
                    uuid_list = []

                with ThreadPoolExecutor(max_workers=15) as pool:
                    pool.map(iter_usercache, usercache)

        concat_db()
        return playerdata_list


    # List Types: ops, bans, wl, subnets (None returns all types)
    # (Optional list type) --> {
    #    'ops': [AclRule, AclRule, ...],
    #    'bans': [AclRule, AclRule, ...],
    #    'wl': [AclRule, AclRule, ...],
    #    'subnets': [AclRule, AclRule, ...]
    # }


    # Iterates over rule_list to prevent removing global rules
    def _iter_rule_list(self, list_type: str, rule_list: str or list):

        if isinstance(rule_list, str):
            new_rules = [rule.strip() for rule in rule_list.split(",")]
        else:
            new_rules = [rule.strip() for rule in rule_list]

        for new_rule in new_rules:
            if list_type == 'bans' and new_rule.count('.') >= 3:
                rule = self.rule_in_acl(new_rule, 'subnets')
            else:
                rule = self.rule_in_acl(new_rule, list_type)

            if rule:
                if rule.rule_scope == 'global':
                    new_rules.remove(new_rule)

        return ', '.join(new_rules)


    # Updates ACL information from server log when player joins/leaves
    def _process_log(self, log_object):

        def generate_dict(*args):

            uuid_dict = get_uuid(log_object['user'])
            location = None
            if log_object['logged-in']:
                location = ip_info(log_object['ip'])

            user_dict = {
                'uuid': uuid_dict['uuid'],
                'name': uuid_dict['name'],
                'latest-ip': log_object['ip'],
                'latest-login': log_object['date'].strftime('%Y-%m-%d %H:%M:%S')
            }

            if location:
                user_dict['ip-geo'] = location

            if user_dict['name'] and user_dict['uuid']:
                temp_folder = os.path.join(cache_folder, 'uuid-temp')
                constants.folder_check(temp_folder)

                with open(
                    os.path.join(temp_folder, f"uuid-{user_dict['uuid'].lower().replace('-', '')}.json"),
                    "w"
                ) as f:

                    f.write(json.dumps(user_dict, indent=2))

            concat_db()

            # Update playerdata internally
            if log_object['logged-in']:
                self.playerdata = self._get_playerdata()
                self.list_items = self._gen_list_items()

        timer = threading.Timer(0, generate_dict)
        timer.start()


    # Generates rule lists that show up in the ACL manager
    # Sort defaults to A-Z (case-insensitive)
    def _gen_list_items(self, list_type=None, invert_sort=False):

        list_dict = {
            'ops': None,
            'bans': None,
            'wl': None
        }

        try:
            banned_ips = gen_iplist(self.rules['subnets'])
        except AttributeError:
            banned_ips = []

        def create_list(list_name):
            sub_list = {'enabled': [], 'disabled': []}

            # Creates container for rule lists
            def create_rule_dict():
                rule_dict = {
                    'global': {'ips': [], 'players': []},
                    'local': {'ips': [], 'players': []}
                }
                return rule_dict

            # Function to sort rule lists
            def sort_rule_list(rule_list, rule_type='player'):
                if rule_type == 'player':
                    return sorted(rule_list, key=lambda d: str.casefold(d.rule), reverse=invert_sort)

                elif rule_type == 'ip':
                    def format_ip(ip):
                        ip = ip.replace('!w', '').strip()
                        try:
                            ip_object = ipaddress.IPv4Address(ip)
                        except ipaddress.AddressValueError:
                            ip_object = ipaddress.IPv4Network(ip)
                        return ip_object

                    return sorted(
                        sorted(rule_list, key=lambda d: str.casefold(d.rule), reverse=invert_sort),
                        key=lambda d: (isinstance(format_ip(d.rule), ipaddress.IPv4Address)), reverse=invert_sort
                    )

            enabled_dict = create_rule_dict()
            disabled_dict = create_rule_dict()


            # Process and sort enabled rules ---------------------------------------------------------------

            if list_name in ['bans', 'subnets']:
                list_name = 'bans'

                for rule in self.rules['subnets']:
                    if "!w" in rule.rule:
                        rule.list_enabled = False
                        disabled_dict[rule.rule_scope]['ips'].append(rule)
                    else:
                        rule.list_enabled = True
                        enabled_dict[rule.rule_scope]['ips'].append(rule)

                for rule in self.rules['bans']:
                    rule.list_enabled = True
                    enabled_dict[rule.rule_scope]['players'].append(rule)

            else:
                for rule in self.rules[list_name]:
                    rule.list_enabled = True
                    enabled_dict[rule.rule_scope]['players'].append(rule)


            if not invert_sort:
                sub_list['enabled'].extend(sort_rule_list(enabled_dict['global']['ips'], rule_type='ip'))
                sub_list['enabled'].extend(sort_rule_list(enabled_dict['global']['players']))
                sub_list['enabled'].extend(sort_rule_list(enabled_dict['local']['ips'], rule_type='ip'))
                sub_list['enabled'].extend(sort_rule_list(enabled_dict['local']['players']))
            else:
                sub_list['enabled'].extend(sort_rule_list(enabled_dict['local']['players']))
                sub_list['enabled'].extend(sort_rule_list(enabled_dict['local']['ips'], rule_type='ip'))
                sub_list['enabled'].extend(sort_rule_list(enabled_dict['global']['players']))
                sub_list['enabled'].extend(sort_rule_list(enabled_dict['global']['ips'], rule_type='ip'))


            # Process and sort disabled rules --------------------------------------------------------------

            # Get lists of UUID's and names for filtering
            enabled_rule_names = [rule.rule.lower() for rule in sub_list['enabled']]
            enabled_rule_uuids = []
            for rule in sub_list['enabled']:
                try:
                    enabled_rule_uuids.append(rule.extra_data['uuid'].lower())
                except KeyError:
                    continue

            # Filter rules that already exist
            for rule in self.playerdata:
                if rule.rule_type == 'player':
                    try:
                        if rule.extra_data['uuid'].lower() in enabled_rule_uuids:
                            continue
                    except KeyError:
                        pass

                if rule.rule.lower() in enabled_rule_names:
                    continue

                # Add users to ban list if IP is banned
                try:
                    if list_name in ['bans', 'subnets'] and rule.rule_type == "player":
                        if get_uuid(rule.rule)["latest-ip"].split(":")[0] in banned_ips:
                            new_rule = deepcopy(rule)
                            new_rule.list_enabled = True
                            enabled_dict[new_rule.rule_scope]['players'].append(new_rule)
                            continue
                except:
                    pass

                rule.list_enabled = False
                disabled_dict[rule.rule_scope]['players'].append(rule)


            # Sort all rules -------------------------------------------------------------------------------------------

            # Resort enabled list to account for added IP bans
            if list_name in ['bans', 'subnets']:
                sub_list['enabled'] = []
                if not invert_sort:
                    sub_list['enabled'].extend(sort_rule_list(enabled_dict['global']['ips'], rule_type='ip'))
                    sub_list['enabled'].extend(sort_rule_list(enabled_dict['global']['players']))
                    sub_list['enabled'].extend(sort_rule_list(enabled_dict['local']['ips'], rule_type='ip'))
                    sub_list['enabled'].extend(sort_rule_list(enabled_dict['local']['players']))
                else:
                    sub_list['enabled'].extend(sort_rule_list(enabled_dict['local']['players']))
                    sub_list['enabled'].extend(sort_rule_list(enabled_dict['local']['ips'], rule_type='ip'))
                    sub_list['enabled'].extend(sort_rule_list(enabled_dict['global']['players']))
                    sub_list['enabled'].extend(sort_rule_list(enabled_dict['global']['ips'], rule_type='ip'))

            # Sort disabled list
            if not invert_sort:
                sub_list['disabled'].extend(sort_rule_list(disabled_dict['global']['ips'], rule_type='ip'))
                sub_list['disabled'].extend(sort_rule_list(disabled_dict['global']['players']))
                sub_list['disabled'].extend(sort_rule_list(disabled_dict['local']['ips'], rule_type='ip'))
                sub_list['disabled'].extend(sort_rule_list(disabled_dict['local']['players']))
            else:
                sub_list['disabled'].extend(sort_rule_list(disabled_dict['local']['players']))
                sub_list['disabled'].extend(sort_rule_list(disabled_dict['local']['ips'], rule_type='ip'))
                sub_list['disabled'].extend(sort_rule_list(disabled_dict['global']['players']))
                sub_list['disabled'].extend(sort_rule_list(disabled_dict['global']['ips'], rule_type='ip'))


            del enabled_dict
            del disabled_dict
            list_dict[list_name] = sub_list


        # If specific list, generate that solely
        if list_type:
            create_list(list_type)

        # If no type specified, thread all of them
        else:
            with ThreadPoolExecutor(max_workers=3) as pool:
                pool.map(create_list, ['ops', 'bans', 'wl'])

        # # Test print
        # if list_dict['ops'] or list_dict['bans'] or list_dict['wl']:
        #     for item in list_dict.keys():
        #         print('enabled', item, [rule.rule for rule in list_dict[item]['enabled']], '\n')
        #         print('disabled', item, [rule.rule for rule in list_dict[item]['disabled']], '\n\n\n')

        return list_dict


    # Sanitizes user input and processes rules accordingly
    # "Name1, !g Name2, 192.168.1.0/24, !w 10.1.1.2"
    # !g denotes global rule, !w denotes whitelisted IP
    # This function is to be passed from a search bar as it can't remove rules
    def _process_query(self, search_list: str or list, list_type=""):

        final_list = {'global': [], 'local': []}
        cache_lookup = None

        # Adds items to final_list without collisions
        def add_entry(rule):

            if global_rule:
                if rule.lower() not in [item.lower() for item in final_list['global']]:
                    final_list['global'].append(rule)

                    # Force global rules to override local ones
                    for x, item in enumerate(final_list['local'], 0):
                        if item.lower() == rule.lower():
                            final_list['local'].pop(x)
            else:
                if rule.lower() not in [item.lower() for item in final_list['local']]:
                    final_list['local'].append(rule)

        # Input validation for each entry in search_list
        if isinstance(search_list, str):
            new_rules = [rule.strip() for rule in search_list.split(",")]
        else:
            new_rules = [rule.strip() for rule in search_list]

        for entry in new_rules:
            global_rule = False
            whitelist = False
            rule_type = "player"

            # Check for global flag
            if "!g" in entry:
                entry = entry.replace('!g', '', 1).strip()
                global_rule = True

            # Check for whitelist tag
            if "!w" in entry:
                entry = entry.replace('!w', '', 1).strip()
                whitelist = True

            # Check if entry is an IP address
            if entry.count(".") >= 3:
                test_entry = entry.strip()

                if "-" in test_entry:
                    test_entry = min_network(test_entry)
                    entry = test_entry

                if constants.check_ip(test_entry, False) or constants.check_subnet(test_entry):
                    rule_type = 'ip'

                # Fix invalid subnets
                if "/" in entry and entry.count(".") == 3:
                    new_network = ipaddress.ip_network(entry, False)
                    entry = f"{new_network.network_address}/{new_network.prefixlen}"


            # Filter IP addresses
            if rule_type == 'ip':

                entry = re.sub('[^0-9./-]', '', entry).strip()

                # Ignore IPs outside a ban list, else find a username in usercache.json
                if list_type not in ['bans', 'subnets']:

                    if not cache_lookup:
                        with open(uuid_db, 'r') as f:
                            cache_lookup = json.loads(f.read())

                    for item in cache_lookup:
                        try:
                            found_ip = item['latest-ip'] if ":" not in item['latest-ip'] else item['latest-ip'].split(':')[0]

                            if ipaddress.IPv4Address(found_ip) in ipaddress.ip_network(entry, False):
                                add_entry(item['name'])

                        except KeyError:
                            pass

                    continue

            # Filter player names
            else:
                is_geyser_user = entry.startswith('.')
                entry = re.sub('[^a-zA-Z0-9 _]', '', entry).strip()
                if is_geyser_user:
                    entry = f'.{entry}'

            # Add entries to final_list
            if whitelist and rule_type == "ip":
                entry = "!w" + entry
            add_entry(entry)


        # Process rules by list_type
        if final_list['global']:
            self.add_global_rule(', '.join(final_list['global']), list_type=list_type)

        if final_list['local']:
            if list_type in ['bans', 'subnets']:
                self.ban_player(', '.join(final_list['local']))
            elif list_type == 'ops':
                self.op_player(', '.join(final_list['local']))
            elif list_type == 'wl':
                self.whitelist_player(', '.join(final_list['local']))

        return final_list


    # Generates AclRule objects from server files
    def _load_acl(self, list_type=None, force_version=None, new_server=False, temp_server=False):

        # If it's a new server, generate acl_dict from only the global rules
        if new_server:

            acl_dict = {
                'ops': [],
                'bans': [],
                'wl': [],
                'subnets': []
            }

            global_acl = load_global_acl()

            for acl_list in global_acl.keys():
                for rule in global_acl[acl_list]:

                    if isinstance(rule, dict):
                        rule = get_uuid(rule['name'])

                        acl_object = check_global_acl(global_acl, AclRule(rule=rule['name'], acl_group=acl_list))

                        for key, value in rule.items():
                            if key != 'name':
                                acl_object.extra_data[key] = value

                    else:
                        acl_object = check_global_acl(global_acl, AclRule(rule=rule, acl_group=acl_list))

                    acl_dict[acl_list].append(acl_object)


        # Get normal ACL dict from server files
        else:
            acl_dict = load_acl(self._server['name'], list_type, force_version, temp_server=temp_server)

        self.list_items = self._gen_list_items()
        return acl_dict


    # Retrieves rule from name and overwrites self.displayed_rule with server-wide rule information
    # rule_name --> AclRule
    def get_rule(self, rule_name: str):

        # Add specific data for IP rules
        if rule_name.count(".") == 3:

            display_data = {
                'rule_info': "",
                'affected_users': 0,
                'ip_range': "",
                'subnet_mask': ""
            }

            # Generate IP address info
            ip_obj = ipaddress.ip_network(rule_name.replace("!w", "").strip(), False)

            if "!w" in rule_name:
                display_data['rule_info'] = constants.translate("Subnet whitelist" if "/" in rule_name else "IP whitelist")
            else:
                display_data['rule_info'] = constants.translate("Subnet ban" if "/" in rule_name else "IP ban")

            display_data['ip_range'] = f"{ip_obj.network_address} - {ip_obj.broadcast_address}"
            display_data['subnet_mask'] = str(ip_obj.netmask)

            # Check uuid-db for affected users
            try:
                with open(uuid_db, 'r') as f:
                    for user in json.loads(f.read()):
                        try:
                            if ipaddress.IPv4Address(user['latest-ip'].split(':')[0]) in ip_obj:
                                display_data['affected_users'] += 1
                        except:
                            continue

            except FileNotFoundError:
                pass

            # Build AclRule object
            final_rule = AclRule(rule=rule_name, acl_group='view')


        # Add specific data for user rules
        else:

            display_data = {
                'effective_access': constants.translate("Normal access"),
                'ban': False,
                'ip_ban': False,
                'op': False,
                'wl': False
            }

            # Audit effective access into display_data
            user = get_uuid(rule_name)

            # Check if player is an operator
            for rule in self.rules['ops']:

                # Check UUID first
                try:
                    if user['uuid'] and user['uuid'] == rule.extra_data['uuid']:
                        display_data['op'] = True
                        break
                except KeyError:
                    pass

                # Then compare rule names
                if user['name'].lower() == rule.rule.lower():
                    display_data['op'] = True
                    break

            # Check if player is banned
            for rule in self.rules['bans']:

                # Check UUID first
                try:
                    if user['uuid'] and user['uuid'] == rule.extra_data['uuid']:
                        display_data['ban'] = True
                        break
                except KeyError:
                    pass

                # Then compare rule names
                if user['name'].lower() == rule.rule.lower():
                    display_data['ban'] = True
                    break

            # Check if player is whitelisted
            for rule in self.rules['wl']:

                # Check UUID first
                try:
                    if user['uuid'] and user['uuid'] == rule.extra_data['uuid']:
                        display_data['wl'] = True
                        break
                except KeyError:
                    pass

                # Then compare rule names
                if user['name'].lower() == rule.rule.lower():
                    display_data['wl'] = True
                    break

            # Check if player is IP banned
            try:
                ip_test = user['latest-ip'].split(':')[0]
                banned_ips = []

                # Check banned IP file if server exists
                if not self._new_server and self.rules['subnets'] and bool(
                    glob(os.path.join(self._server['path'], '*banned-ips*'))):

                    if constants.version_check(self._server['version'], '<', constants.json_format_floor):
                        with open(os.path.join(self._server['path'], 'banned-ips.txt'), 'r') as f:
                            # Make sure this will replace line breaks on Linux IP lists as well
                            banned_ips = [ip.replace('\n', '') for ip in f.readlines() if ip.replace('\n', '')]
                    else:
                        with open(os.path.join(self._server['path'], 'banned-ips.json'), 'r') as f:
                            banned_ips = [ip['ip'] for ip in json.loads(f.read()) if ip['ip']]

                # If new server, generate the rules and then check
                elif self.rules['subnets']:
                    banned_ips = gen_iplist(self.rules['subnets'])

                if ip_test in banned_ips:
                    display_data['ip_ban'] = True

            except KeyError:
                pass

            # Generate effective access principle
            if display_data['ban'] or display_data['ip_ban']:
                display_data['effective_access'] = constants.translate("No access")

            else:
                if self._server['whitelist'] and not (display_data['wl'] or display_data['op']):
                    display_data['effective_access'] = constants.translate("No access")

                elif display_data['op']:
                    display_data['effective_access'] = constants.translate("Operator access")

            # Build AclRule object
            try:
                user['ip-geo']

            # Eventually set these to "retrieving info..." and make function to load all server latest.logs. also make algorithm to keep the newest date when iterating over every server
            except KeyError:
                user['latest-ip'] = constants.translate("Unknown")
                user['latest-login'] = constants.translate("Unknown")
                user['ip-geo'] = constants.translate("Unknown")

            # Create algorithm when servers exist to change this dynamically
            user['online'] = False

            final_rule = AclRule(rule=user['name'], acl_group='view')
            for data in user.keys():
                final_rule.extra_data[data] = user[data]

        # Set display rule to AclRule object
        final_rule.display_data = display_data
        self.displayed_rule = final_rule

        return final_rule


    # Checks if rule name is inside of self.rules[list_type]
    # Returns None or rule if found
    def rule_in_acl(self, rule_name: str, list_type: str):

        found_rule = None
        rule_name = rule_name.strip()

        if list_type in ['ops', 'bans', 'wl', 'subnets']:

            if list_type == 'subnets':
                for rule in self.rules[list_type]:
                    if rule_name.lower() == rule.rule.lower():
                        found_rule = rule
                        break

            else:
                user = get_uuid(rule_name)

                for rule in self.rules[list_type]:
                    try:
                        if user['uuid'] and rule.extra_data['uuid'] == user['uuid']:
                            found_rule = rule
                            break

                    except KeyError:
                        pass

                    if found_rule is None:
                        if user['name'].lower() == rule.rule.lower():
                            found_rule = rule
                            break

        return found_rule


    # Counts rules inside specified list, or all lists if unspecified
    # Returns --> {list_type: int}
    def count_rules(self, list_type=None):

        if list_type:
            list_type = 'bans' if list_type == 'subnets' else list_type
            num_dict = {list_type: len(self.rules[list_type])}
            if list_type == 'bans':
                num_dict['list_type'] += len(self.rules['subnets'])
            elif list_type == 'wl' and not self._server['whitelist']:
                num_dict['wl'] = 0

        else:
            num_dict = {
                'ops': len(self.rules['ops']),
                'bans': len(self.rules['bans']) + len(self.rules['subnets']),
                'wl': len(self.rules['wl']) if self._server['whitelist'] else 0
            }
            num_dict['total'] = num_dict['ops'] + num_dict['bans'] + num_dict['wl']

        return num_dict



    # Note:  the *_user functions below return the entire ACL dict, not just rule_list

    # Kick a player or list of players
    def kick_player(self, rule_list: str or list or PlayerScriptObject, reason=None):
        if self._server['name'] not in constants.server_manager.running_servers:
            return False

        # Process rule list
        rule_list = convert_obj_to_str(rule_list)
        if isinstance(rule_list, str):
            rule_list = [p.strip() for p in rule_list.split(',')]

        # Format kick reason
        if isinstance(reason, str):
            reason = ' ' + reason
        else:
            reason = ''

        server_obj = constants.server_manager.running_servers[self._server['name']]
        if server_obj.running:
            for player in rule_list:
                server_obj.silent_command(f'kick {player}{reason}')
            return True
        return False

    # op_player("BlUe_KAZoo, kchicken, test")
    # "Rule1, Rule2" --> [AclObject1, AclObject2]
    def op_player(self, rule_list: str or list or PlayerScriptObject, remove=False, force_version=None, temp_server=False):
        rule_list = convert_obj_to_str(rule_list)

        # Ignore removal of global rules
        if remove:
            rule_list = self._iter_rule_list('ops', rule_list)

        # Only modify rules if new server
        if self._new_server:
            self.edit_list(rule_list, 'ops', remove)

        # Normal behavior
        else:
            op_list = op_user(self._server['name'], rule_list, remove, force_version, True, temp_server)
            self.rules['ops'] = op_list

        self.list_items = self._gen_list_items()
        return self.rules

    # ban_player("KChicken, 192.168.1.2, 192.168.0.0/24, !w 192.168.0.69, !w 192.168.0.128/28, 10.1.1.0-37")
    # "Rule1, Rule2" --> [AclObject1, AclObject2]
    def ban_player(self, rule_list: str or list or PlayerScriptObject, remove=False, reason=None, length='forever', force_version=None, temp_server=False):
        rule_list = convert_obj_to_str(rule_list)

        # Format ban reason
        if isinstance(reason, str) and not remove:
            reason = ' ' + reason
        else:
            reason = ''

        # Ignore removal of global rules
        if remove:
            rule_list = self._iter_rule_list('bans', rule_list)


        # Only modify rules if new server
        if self._new_server:
            self.edit_list(rule_list, 'bans', remove)

        # Normal behavior
        else:
            ban_list, subnet_list = ban_user(self._server['name'], rule_list, remove, force_version, True, temp_server, reason, length)
            self.rules['bans'] = ban_list
            self.rules['subnets'] = subnet_list

        self.list_items = self._gen_list_items()
        return self.rules

    # whitelist_player("BlUe_KAZoo, kchicken, test")
    # "Rule1, Rule2" --> [AclObject1, AclObject2]
    def whitelist_player(self, rule_list: str or list or PlayerScriptObject, remove=False, force_version=None, temp_server=False):
        rule_list = convert_obj_to_str(rule_list)

        # Ignore removal of global rules
        if remove:
            rule_list = self._iter_rule_list('wl', rule_list)


        # Only modify rules if new server
        if self._new_server:
            self.edit_list(rule_list, 'wl', remove)

        # Normal behavior
        else:
            wl_list, op_list = wl_user(self._server['name'], rule_list, remove, force_version, True, temp_server)
            self.rules['wl'] = wl_list

            if op_list:
                self.rules['ops'] = op_list

        self.list_items = self._gen_list_items()
        return self.rules

    # Toggles whitelist on or off
    def enable_whitelist(self, enabled=True):
        if isinstance(enabled, bool):

            if not self._new_server:
                new_properties = constants.server_properties(self._server['name'])
                new_properties['white-list'] = enabled
                try:
                    new_properties['enforce-whitelist'] = enabled
                except KeyError:
                    pass
                constants.server_properties(self._server['name'], new_properties)

            self._server['whitelist'] = enabled
            self.whitelist_enabled = enabled

            # If server is running, reload whitelist settings in memory
            if self._server['name'] in constants.server_manager.running_servers:
                server_obj = constants.server_manager.running_servers[self._server['name']]
                if server_obj.running:
                    server_obj.silent_command(f'whitelist {"on" if enabled else "off"}', log=False)
                    server_obj.silent_command(f'whitelist reload', log=False)

    # Adds rule list to global ACL, then to every server (use similar to the *_user functions)
    # add_global_rule("BlUe_KAZoo, kchicken, test", list_type="ops", remove=False) --> self.rules
    # List Types: ops, bans, wl
    def add_global_rule(self, rule_list: str or list or PlayerScriptObject, list_type: str, remove=False):
        rule_list = convert_obj_to_str(rule_list)

        add_global_rule(rule_list, list_type, remove)

        if self._new_server:
            self.edit_list(rule_list, list_type, remove, overwrite=True)
            self.edit_list(rule_list, list_type, remove)

        else:

            if list_type in ['bans', 'subnets']:
                self.rules['bans'] = self._load_acl('bans')
                self.rules['subnets'] = self._load_acl('subnets')
            else:
                self.rules[list_type] = self._load_acl(list_type)

        self.list_items = self._gen_list_items()
        return self.rules


    # Reloads ACL contents
    # List Types: ops, bans, wl
    def reload_list(self, list_type=None):

        if list_type == 'ops' or not list_type:
            self.rules['ops'] = self._load_acl('ops')
            if list_type:
                return

        if list_type == 'wl' or not list_type:
            self.rules['wl'] = self._load_acl('wl')
            if list_type:
                return

        if list_type in ['bans', 'subnets'] or not list_type:
            self.rules['bans'] = self._load_acl('bans')
            self.rules['subnets'] = self._load_acl('subnets')


    # Note:  below methods are specifically for new servers

    # Operates similarly to *_user rules, but only edits self.rules[list_type]
    # List Types: ops, bans, wl
    def edit_list(self, rule_list: str or list or PlayerScriptObject, list_type: str, remove=False, overwrite=False):
        rule_list = convert_obj_to_str(rule_list)

        list_type = 'bans' if list_type == 'subnets' else list_type

        if isinstance(rule_list, str):
            new_rules = [rule.strip() for rule in rule_list.split(",")]
        else:
            new_rules = [rule.strip() for rule in rule_list]

        global_acl = load_global_acl()


        # Iterate over all rules in rule_list
        if new_rules:
            for rule in new_rules:

                # If rule is an IP, edit subnet list
                if rule.count('.') >= 3:
                    if list_type == 'bans':
                        rule_in_list = self.rule_in_acl(rule, 'subnets')

                        if (remove or overwrite) and rule_in_list:
                            self.rules['subnets'].remove(rule_in_list)

                        if (not remove and not rule_in_list) or overwrite:
                            acl_object = AclRule(rule, acl_group='subnets')
                            self.rules['subnets'].append(check_global_acl(global_acl, acl_object))


                # If rule is a player, edit list_type
                else:
                    rule_in_list = self.rule_in_acl(rule, list_type)

                    if (remove or overwrite) and rule_in_list:
                        self.rules[list_type].remove(rule_in_list)

                    if (not remove and not rule_in_list) or overwrite:
                        user = get_uuid(rule)
                        acl_object = check_global_acl(global_acl, AclRule(rule=user['name'], acl_group=list_type))
                        for data in user.keys():
                            acl_object.extra_data[data] = user[data]

                        self.rules[list_type].append(acl_object)


        # # Dirty fix to prevent IPs from filling ban list for some reason
        # if list_type == 'bans':
        #     self.rules['bans'] = [rule for rule in self.rules['bans'] if rule.rule.count(".") < 3]


    # Writes self.rules to appropriate files in server path (primarily for new servers)
    def write_rules(self):

        constants.folder_check(constants.tmpsvr if self._new_server else self._server['path'])

        # Override write functionality for new server
        new_server = bool(self._new_server)
        self._new_server = False


        if self.rules['bans'] or self.rules['subnets']:
            ban_list = [rule.rule for rule in self.rules['bans']]
            ban_list.extend([rule.rule for rule in self.rules['subnets']])
            self.ban_player(', '.join(ban_list), force_version=self._server['version'], temp_server=new_server)

        if self.rules['ops']:
            self.op_player(', '.join([rule.rule for rule in self.rules['ops']]), force_version=self._server['version'], temp_server=new_server)

        if self.rules['wl']:
            self.whitelist_player(', '.join([rule.rule for rule in self.rules['wl']]), force_version=self._server['version'], temp_server=new_server)

        self._new_server = new_server

# ---------------------------------------------- General Functions -----------------------------------------------------

# IP, subnet --> boolean
def in_subnet(ip: str, cidr: str):
    return ipaddress.IPv4Address(ip) in ipaddress.IPv4Network(cidr)


# Returns count of IPs in network
def count_subnet(network: str):
    return ipaddress.IPv4Network(network).num_addresses


# Returns the smallest possible subnet for an IP range
# 10.1.1.4-20 --> subnet
def min_network(ip_range: str):

    def get_prefix_length(number1, number2, bits):
        """Get the number of leading bits that are same for two numbers.
        Args:
            number1: an integer.
            number2: another integer.
            bits: the maximum number of bits to compare.
        Returns:
            The number of leading bits that are the same for two numbers.
        """
        for i in range(bits):
            if number1 >> i == number2 >> i:
                return bits - i
        return 0

    ip_a, ip_b = ip_range.split("-")

    if ip_b.count(".") != 3:
        ip_b = ip_a.rsplit(".", 1)[0] + "." + ip_b

    # Look at larger and smaller IP addresses
    try:
        ips = [ipaddress.IPv4Address(ip_a), ipaddress.IPv4Address(ip_b)]
        lowest_ip, highest_ip = min(ips), max(ips)

        mask_length = get_prefix_length(int(lowest_ip), int(highest_ip), lowest_ip.max_prefixlen)

        # Return the network
        network_ip = ipaddress.ip_network("%s/%d" % (lowest_ip, mask_length), strict=False).network_address
        network = ipaddress.ip_network("%s/%d" % (network_ip, mask_length), strict=True)
        return str(network)

    except ipaddress.AddressValueError:
        return None


# Resolves geolocation of IP addresses
# IP address --> location string
def ip_info(addr: str):

    addr = addr.split(":")[0]
    addr = "127.0.0.1" if addr == "localhost" else addr
    location = ""

    if constants.check_ip(addr, False):

        ip_obj = ipaddress.IPv4Address(addr)

        if ip_obj.is_private:
            private_ip = socket.gethostbyname(socket.gethostname())

            if ip_obj.is_loopback or addr == private_ip:
                location = "This machine"

            else:
                location = "LAN device"

        else:
            try:
                url = f'https://ipinfo.io/{addr}/json'
                response = urlopen(url)
                data = json.load(response)

                city = data['city']
                country = data['country']
                region = data['region']

                location = f"{city}, {region} - {country}"

            except:
                location = None

    return location


# name --> version, path
def dump_config(server_name: str, new_server=False):

    server_dict = {
        'name': server_name,
        'version': None,
        'path': None,
        'world': None,
        'whitelist': False
    }

    server_version = None
    level_name = None
    server_path = constants.server_path(server_name)
    config_file = constants.server_path(server_name, constants.server_ini)
    properties_file = constants.server_path(server_name, 'server.properties')


    # Check auto-mcs.ini for info
    if config_file and os.path.isfile(config_file):
        try:
            server_config = constants.server_config(server_name)
        except:
            time.sleep(0.1)
            server_config = constants.server_config(server_name)

        # Only pickup server as valid with good config
        if server_name == server_config.get("general", "serverName"):
            server_version = server_config.get("general", "serverVersion")


    # Check server.properties for info
    if properties_file and os.path.isfile(properties_file):
        server_properties = constants.server_properties(server_name)

        try:
            server_dict['world'] = server_properties['level-name']
            server_dict['whitelist'] = server_properties['white-list']
        except KeyError:
            server_dict['world'] = 'world'
            server_dict['whitelist'] = False


    if new_server:
        server_dict['version'] = constants.new_server_info['version']
        server_dict['path'] = os.path.join(constants.applicationFolder, 'Servers', server_name)
    else:
        server_dict['version'] = server_version
        server_dict['path'] = server_path

    return server_dict


# Generates list of IP addresses from a list of AclRule rules
# rule_list --> [for IP in subnet if not in whitelist]
def gen_iplist(rule_list: list):

    final_list = []

    # Finds every address on a subnet
    def iter_network(network_addr):

        ip, sm = network_addr.split("/")

        if constants.check_ip(ip, False):
            network_object = ipaddress.IPv4Network(network_addr)
            return [str(ip) for ip in ipaddress.IPv4Network(network_addr, strict=False) if str(ip) not in [str(network_object.network_address), str(network_object.broadcast_address)]]


    # Multithreaded iter_network to final list
    def gen_range(network):
        final_list.extend(iter_network(network))


    # Multithreaded remove whitelists from final list
    def check_wl(addr):

        if "/" in addr:
            for ip in iter_network(addr):
                if ip in final_list:
                    final_list.remove(ip)

        if addr in final_list:
            final_list.remove(addr)


    # Run multithreaded functions

    # List of strings
    subnets = [x.rule for x in rule_list if ("/" in x.rule) and ("!w" not in x.rule)]

    # List of strings
    whitelists = [x.rule.replace("!w", "") for x in [x for x in rule_list if "!w" in x.rule]]

    # List of AclObjects
    ip_list = [x for x in rule_list if (x.rule.count('.') == 3) and ("!w" not in x.rule) and ("/" not in x.rule)]


    if subnets:
        with ThreadPoolExecutor(max_workers=15) as pool:
            pool.map(gen_range, subnets)

    if ip_list:
        no_object_list = list(tuple(final_list))
        for addr in ip_list:
            if addr.rule not in no_object_list:
                final_list.append(addr if isinstance(addr, str) else addr.rule)
                no_object_list.append(addr.rule)

    if whitelists:
        with ThreadPoolExecutor(max_workers=15) as pool:
            pool.map(check_wl, whitelists)

    # print(subnets, whitelists, ip_list)
    # print(final_list)

    # Note:  ip_list will mix strings and AclObjects to preserve ban metadata for singular IP bans,
    # and strings to optimize speed/memory for calculating large subnets
    return final_list


# Specifically for testing/viewing load_acl() objects
def print_acl(acl_object: AclManager):
    print(f"# {'='*60}>  {acl_object.server['name']} - ACL  <{'='*60} #\n\n")
    acl_dict = acl_object.rules
    print("Server Information:\n\n" + f"    New Server: {acl_object._new_server}\n" + "    " + str(acl_object.server) + "\n\n")
    if acl_dict['ops']:
        print(f"Operators - {len(acl_dict['ops'])} rule(s):\n")
        print('    ' + '\n    '.join([str(vars(rule)) for rule in acl_dict['ops']]), end="\n\n\n")
    if acl_dict['bans']:
        print(f"Bans - {len(acl_dict['bans'])} rule(s):\n")
        print('    ' + '\n    '.join([str(vars(rule)) for rule in acl_dict['bans']]), end="\n\n\n")
    if acl_dict['wl']:
        print(f"Whitelist - {len(acl_dict['wl'])} rule(s):\n")
        print('    ' + '\n    '.join([str(vars(rule)) for rule in acl_dict['wl']]), end="\n\n\n")
    if acl_dict['subnets']:
        print(f"Banned IPs - {len(acl_dict['subnets'])} rule(s):\n")
        print('    ' + '\n    '.join([str(vars(rule)) for rule in acl_dict['subnets']]), end="\n\n\n")


# Check if user is online
def check_online(user):

    def pool_func(server, *args):
        print(server.run_data['player-list'])
        test = False
        try:
            test = bool(server.run_data['player-list'][user]['logged-in'])
        except KeyError:
            pass
        return test

    with ThreadPoolExecutor(max_workers=10) as pool:
        for item in pool.map(pool_func, [server for server in constants.server_manager.running_servers.values() if server.running]):
            if item:
                return True
        return False



# -------------------------------------------- Global ACL functions ----------------------------------------------------

# Retrieves and returns contents of global ACL
def load_global_acl():

    global_acl = {
        'ops': [],
        'bans': [],
        'wl': [],
        'subnets': []
    }

    if os.path.isfile(global_acl_file):
        with open(global_acl_file, 'r') as f:
            global_acl = json.load(f)

    return global_acl


# Check if global_acl contains AclRule
# global_acl, AclRule --> AclRule
def check_global_acl(global_acl: dict, acl_rule: AclRule):

    # Check OPs
    if acl_rule.acl_group == "ops":
        try:
            acl_rule.set_scope(acl_rule.rule.lower() in [rule['name'].lower() for rule in global_acl["ops"]])
        except KeyError:
            pass

    # Check banned users
    elif acl_rule.acl_group == "bans":
        try:
            acl_rule.set_scope(acl_rule.rule.lower() in [rule['name'].lower() for rule in global_acl["bans"]])
        except KeyError:
            pass

    # Check whitelisted users
    elif acl_rule.acl_group == "wl":
        try:
            acl_rule.set_scope(acl_rule.rule.lower() in [rule['name'].lower() for rule in global_acl["wl"]])
        except KeyError:
            pass

    # Check banned IPs/subnets
    else:
        acl_rule.set_scope(acl_rule.rule in global_acl["subnets"])


    return acl_rule


# Adds rule list to global ACL, then to every server (use similar to the *_user functions)
# add_global_rule("BlUe_KAZoo, kchicken, test", list_type="ops", remove=False) --> global_acl dict
# List Types: ops, bans, wl
def add_global_rule(rule_list: str or list, list_type: str, remove=False):

    global_acl = load_global_acl()
    server_list = constants.generate_server_list()

    if isinstance(rule_list, str):
        rule_list = [rule.strip() for rule in rule_list.split(",")]
    else:
        rule_list = [rule.strip() for rule in rule_list]

    final_rule_list = []

    if list_type in ['bans', 'subnets']:
        list_type = 'bans'
        global_rule_list = deepcopy(global_acl['bans'])
        global_rule_list.extend([{'uuid': None, 'name': rule} for rule in global_acl['subnets']])
    else:
        global_rule_list = deepcopy(global_acl[list_type])


    # Function for threading server rule processing
    def iter_server(server_name):

        if list_type == 'ops':
            op_user(server_name, name_list, remove=remove)

        if list_type == 'bans':
            ban_user(server_name, name_list, remove=remove)

        if list_type == 'wl':
            wl_user(server_name, name_list, remove=remove)


    # Iterate over every user in rule_list and filter them to create final_rule_list
    for rule in rule_list:

        if rule.count(".") == 3:
            user_info = {'uuid': None, 'name': rule}
        else:
            user_info = get_uuid(rule)
            user_info = {'uuid': user_info['uuid'], 'name': user_info['name']}

        # Only remove rules that already exist
        if remove:
            for global_rule in global_rule_list:
                if user_info['uuid']:
                    if user_info['uuid'] == global_rule['uuid']:
                        final_rule_list.append(global_rule)
                        break
                if user_info['name'].lower() == global_rule['name'].lower():
                    final_rule_list.append(global_rule)
                    break

        # Only add rules that don't exist
        else:
            for global_rule in global_rule_list:
                if user_info['uuid']:
                    if user_info['uuid'] == global_rule['uuid']:
                        break
                if user_info['name'].lower() == global_rule['name'].lower():
                    break
            else:
                final_rule_list.append(user_info)


    # Apply rules to global_acl and write file
    for rule in final_rule_list:
        if remove:
            if rule['name'].count(".") == 3:
                global_acl['subnets'].remove(rule['name'])
            else:
                global_acl[list_type].remove(rule)

        else:
            if rule['name'].count(".") == 3:
                global_acl['subnets'].append(rule['name'])
            else:
                global_acl[list_type].append(rule)


    # Write to global acl file
    constants.folder_check(constants.configDir)
    with open(global_acl_file, "w") as f:
        f.write(json.dumps(global_acl, indent=2))


    # Thread rule processing for all servers
    name_list = ', '.join([rule['name'] for rule in final_rule_list])
    with ThreadPoolExecutor(max_workers=20) as pool:
        pool.map(iter_server, server_list)


    # print(global_acl)
    concat_db()
    return global_acl



# ------------------------------------------- ACL specific functions ---------------------------------------------------

# Name or UUID --> {'name': Name, 'uuid': UUID}
def get_uuid(user: str):

    found_item = False
    if len(user.replace("-", "")) == 32:
        final_dict = {'uuid': user, 'name': None}
        user_is_uuid = True
    else:
        final_dict = {'uuid': None, 'name': user}
        user_is_uuid = False


    # First, check if the user exists in uuid-db.json
    if os.path.exists(uuid_db):
        try:
            with open(uuid_db, "r") as f:
                content = f.read()
                try:
                    file = json.loads(content)
                except:

                    # If failure, try to repair the json file
                    try:
                        print("Attempting to fix 'uuid-db.json' due to formatting error")
                        file = json_repair.loads(content)
                        if not file:
                            raise TypeError
                    except:
                        print("'uuid-db.json' reset due to formatting error")
                        file = None
        except OSError:
            file = None

        if file:
            for item in file:
                if (item['uuid'].lower() == user.lower()) or (item['name'].lower() == user.lower()):
                    final_dict = item
                    found_item = True


    # If the user has not been found, check the internet
    if (constants.app_online) and (not found_item):

        try:
            check_url = f"https://mcuuid.net/?q={user.strip()}"
            soup = constants.get_url(check_url)

            final_dict = {
                'uuid': soup.find('input', id='results_id').get('value'),
                'name': soup.find('input', id='results_username').get('value')
            }

            if not final_dict['name'] and not user_is_uuid:
                final_dict['name'] = user

            if final_dict['name'] and final_dict['uuid']:
                temp_folder = os.path.join(cache_folder, 'uuid-temp')
                constants.folder_check(temp_folder)

                with open(
                    os.path.join(temp_folder, f"uuid-{final_dict['uuid'].lower().replace('-', '')}.json"),
                    "w"
                ) as f:

                    f.write(json.dumps(final_dict, indent=2))

        except ConnectionRefusedError:
            pass

    if final_dict['uuid'] is None:
        final_dict['uuid'] = ""

    return final_dict


# Concatenates all files in ..\Cache\uuid-temp\* --> ..\Cache\uuid-db.json
def concat_db(only_delete=False):

    try:
        temp_file = os.path.join(cache_folder, 'uuid-temp')
        uuid_list = []
        final_db = []
        added_items = []


        # Load current uuid-db.json into final_db
        try:
            with open(uuid_db, "r") as f:
                content = f.read()
                try:
                    current_db = json.loads(content)
                except:

                    # If failure, try to repair the json file
                    try:
                        print("Attempting to fix 'uuid-db.json' due to formatting error")
                        current_db = json_repair.loads(content)
                        if not current_db:
                            raise TypeError
                    except:
                        print("'uuid-db.json' reset due to formatting error")
                        current_db = {}
                uuid_list = [item['uuid'] for item in current_db]

        except OSError:
            current_db = []

        final_db = current_db


        # Iterate over every file in uuid-temp
        if os.path.exists(temp_file):
            for item in glob(os.path.join(temp_file, 'uuid-*.json')):

                if not only_delete:
                    try:
                        with open(item, 'r') as f:
                            user = json.load(f)
                            added_items.append(user)

                            if user['uuid'] in uuid_list:
                                found_user = final_db[uuid_list.index(user['uuid'])]
                                found_user['name'] = user['name']
                                try:
                                    found_user['latest-ip'] = user['latest-ip']
                                    found_user['latest-login'] = user['latest-login']
                                    found_user['ip-geo'] = user['ip-geo']
                                except KeyError:
                                    pass

                            else:
                                final_db.append(user)
                                uuid_list = [item['uuid'] for item in final_db]
                    except Exception as e:
                        if constants.debug:
                            print(e)

                try:
                    os.remove(item)
                except PermissionError:
                    if constants.debug:
                        print("Error: could not delete cache")

            with open(uuid_db, "w+") as f:
                f.write(json.dumps(final_db, indent=2))

            constants.safe_delete(temp_file)


            # Check added_items against global ACL to update names
            global_acl = load_global_acl()
            added_uuid_list = [item['uuid'] for item in added_items]

            for user in global_acl['ops']:
                if user['uuid'] in added_uuid_list:
                    updated_user = added_items[added_uuid_list.index(user['uuid'])]
                    if user['name'] != updated_user['name']:
                        add_global_rule(user['name'], list_type='ops', remove=True)
                        add_global_rule(updated_user['name'], list_type='ops')

            for user in global_acl['bans']:
                if user['uuid'] in added_uuid_list:
                    updated_user = added_items[added_uuid_list.index(user['uuid'])]
                    if user['name'] != updated_user['name']:
                        add_global_rule(user['name'], list_type='bans', remove=True)
                        add_global_rule(updated_user['name'], list_type='bans')

            for user in global_acl['wl']:
                if user['uuid'] in added_uuid_list:
                    updated_user = added_items[added_uuid_list.index(user['uuid'])]
                    if user['name'] != updated_user['name']:
                        add_global_rule(user['name'], list_type='wl', remove=True)
                        add_global_rule(updated_user['name'], list_type='wl')

    except FileNotFoundError:
        pass


# Generates AclRule objects from server files
def load_acl(server_name: str, list_type=None, force_version=None, temp_server=False):

    server_properties = dump_config(server_name)
    server_name = server_properties['name']
    version = server_properties['version']
    server_path = constants.tmpsvr if temp_server else server_properties['path']

    if force_version:
        version = force_version

    server_acl = {
        'ops': [],
        'bans': [],
        'wl': [],
        'subnets': []
    }

    global_acl = load_global_acl()
    original_ip_rules = []

    def finalize():
        concat_db()

    # Check for subnets
    if (list_type == "subnets") or not list_type:
        final_path = os.path.join(server_path, "banned-subnets.json")

        if os.path.exists(final_path):
            with open(final_path, "r") as f:
                try:
                    file_contents = json.load(f)

                    # Check that global rules are applied
                    for rule in global_acl['subnets']:
                        if rule.lower().replace(" ", "") not in file_contents:
                            file_contents.append(rule.lower().replace(" ", ""))

                    if file_contents:
                        for subnet in file_contents:

                            if ("!w" not in subnet) and ("/" not in subnet):
                                continue

                            acl_object = check_global_acl(
                                global_acl,
                                AclRule(rule=subnet.replace(" ", "").strip(), acl_group='subnets')
                            )

                            server_acl['subnets'].append(acl_object)
                            original_ip_rules.append(acl_object)

                except OSError:
                    pass

    # Convert old .txt lists ---------------------------------------------------------------------------------------
    if constants.version_check(version, "<", constants.json_format_floor):

        # Check for OPs
        if (list_type == "ops") or not list_type:
            final_path = os.path.join(server_path, "ops.txt")

            if os.path.exists(final_path):
                with open(final_path, "r") as f:
                    file = [line for line in f.read().splitlines() if not line.startswith("#") and line.strip()]

                    # Check that global rules are applied
                    for rule in global_acl['ops']:
                        if rule['name'].lower() not in file:
                            file.append(rule['name'].lower())

                    for user in file:
                        user = get_uuid(user.strip())

                        if len(user) != 0:
                            acl_object = check_global_acl(
                                global_acl,
                                AclRule(rule=user['name'], acl_group='ops')
                            )

                            if user['uuid']:
                                acl_object.extra_data['uuid'] = user['uuid']

                            server_acl['ops'].append(acl_object)

            if list_type == "ops":
                finalize()
                return server_acl['ops']

        # Check for bans
        if (list_type == "bans") or not list_type:

            # Players
            final_path = os.path.join(server_path, "banned-players.txt")

            if os.path.exists(final_path):
                with open(final_path, "r") as f:
                    file = [line for line in f.read().splitlines() if not line.startswith("#") and line.strip()]

                    # Check that global rules are applied
                    for rule in global_acl['bans']:
                        if rule['name'].lower() not in file:
                            file.append(rule['name'].lower())

                    for user in file:
                        user = get_uuid(user.strip())

                        if len(user) != 0:
                            acl_object = check_global_acl(
                                global_acl,
                                AclRule(rule=user['name'], acl_group='bans')
                            )

                            if user['uuid']:
                                acl_object.extra_data['uuid'] = user['uuid']

                            server_acl['bans'].append(acl_object)

            if list_type == "bans":
                finalize()
                return server_acl['bans']

        # Check for whitelist
        if (list_type == "wl") or not list_type:
            final_path = os.path.join(server_path, "white-list.txt")

            if os.path.exists(final_path):
                with open(final_path, "r") as f:
                    file = [line for line in f.read().splitlines() if not line.startswith("#") and line.strip()]

                    # Check that global rules are applied
                    for rule in global_acl['wl']:
                        if rule['name'].lower() not in file:
                            file.append(rule['name'].lower())

                    for user in file:
                        user = get_uuid(user.strip())

                        if len(user) != 0:
                            acl_object = check_global_acl(
                                global_acl,
                                AclRule(rule=user['name'], acl_group='wl')
                            )

                            if user['uuid']:
                                acl_object.extra_data['uuid'] = user['uuid']

                            server_acl['wl'].append(acl_object)

            if list_type == "wl":
                finalize()
                return server_acl['wl']

        # Check for banned IPs
        if (list_type == "subnets") or not list_type:
            final_path = os.path.join(server_path, "banned-ips.txt")

            if os.path.exists(final_path):
                with open(final_path, "r") as f:
                    file = [line for line in f.read().splitlines() if not line.startswith("#") and line.strip()]

                    for user in file:

                        valid_ip = False
                        checked_ip = user

                        # IP rule determination logic
                        for rule in original_ip_rules:
                            rule = rule.rule

                            # Allow singular IP if it's not also whitelisted
                            if rule.replace("!w", "") != checked_ip:
                                valid_ip = True

                            # Allow singular IP if it's not already in an IP range
                            if "/" in rule:
                                valid_ip = not in_subnet(checked_ip, rule.replace("!w", ""))
                                if not valid_ip:
                                    break

                        if len(user) != 0 and valid_ip:
                            acl_object = check_global_acl(
                                global_acl,
                                AclRule(rule=user.strip(), acl_group='subnets')
                            )

                            server_acl['subnets'].append(acl_object)

            if list_type == "subnets":
                finalize()
                return server_acl['subnets']


    # Convert new json lists ---------------------------------------------------------------------------------------
    else:

        # Check for OPs
        if (list_type == "ops") or not list_type:
            final_path = os.path.join(server_path, "ops.json")

            if os.path.exists(final_path):
                with open(final_path, "r") as f:
                    try:
                        file = json.load(f)
                    except json.decoder.JSONDecodeError:
                        file = []

                    # Check that global rules are applied
                    for rule in global_acl['ops']:
                        if rule['uuid'] not in [user['uuid'] for user in file]:
                            file.append(rule)

                    if file:
                        for user in file:
                            acl_object = check_global_acl(
                                global_acl,
                                AclRule(rule=user['name'], acl_group='ops')
                            )

                            try:
                                acl_object.extra_data['uuid'] = user['uuid']
                                acl_object.extra_data['level'] = user['level']
                                acl_object.extra_data['bypassesPlayerLimit'] = user['bypassesPlayerLimit']
                            except KeyError:
                                acl_object.extra_data['uuid'] = user['uuid']
                                acl_object.extra_data['level'] = 4
                                acl_object.extra_data['bypassesPlayerLimit'] = True

                            server_acl['ops'].append(acl_object)

            if list_type == "ops":
                finalize()
                return server_acl['ops']

        # Check for bans
        if (list_type == "bans") or not list_type:

            # Players
            final_path = os.path.join(server_path, "banned-players.json")

            if os.path.exists(final_path):
                with open(final_path, "r") as f:
                    try:
                        file = json.load(f)
                    except json.decoder.JSONDecodeError:
                        file = []

                    # Check that global rules are applied
                    for rule in global_acl['bans']:
                        if rule['uuid'] not in [user['uuid'] for user in file]:
                            file.append(rule)

                    for user in file:
                        acl_object = check_global_acl(
                            global_acl,
                            AclRule(rule=user['name'], acl_group='bans')
                        )

                        try:
                            acl_object.extra_data['uuid'] = user['uuid']
                            acl_object.extra_data['created'] = user['created']
                            acl_object.extra_data['source'] = user['source']
                            acl_object.extra_data['expires'] = user['expires']
                            acl_object.extra_data['reason'] = user['reason']
                        except KeyError:
                            acl_object.extra_data['uuid'] = user['uuid']
                            acl_object.extra_data['created'] = dt.now().strftime("%Y-%m-%d %H:%M:%S +0000")
                            acl_object.extra_data['source'] = "Server"
                            acl_object.extra_data['expires'] = "forever"
                            acl_object.extra_data['reason'] = "Banned by an operator."

                        server_acl['bans'].append(acl_object)

            if list_type == "bans":
                finalize()
                return server_acl['bans']

        # Check for whitelist
        if (list_type == "wl") or not list_type:
            final_path = os.path.join(server_path, "whitelist.json")

            if os.path.exists(final_path):
                with open(final_path, "r") as f:
                    try:
                        file = json.load(f)
                    except json.decoder.JSONDecodeError:
                        file = []

                    # Check that global rules are applied
                    for rule in global_acl['wl']:
                        if rule['uuid'] not in [user['uuid'] for user in file]:
                            file.append(rule)

                    for user in file:
                        acl_object = check_global_acl(
                            global_acl,
                            AclRule(rule=user['name'], acl_group='wl')
                        )

                        acl_object.extra_data['uuid'] = user['uuid']
                        server_acl['wl'].append(acl_object)

            if list_type == "wl":
                finalize()
                return server_acl['wl']

        # Check for banned IPs
        if (list_type == "subnets") or not list_type:
            final_path = os.path.join(server_path, "banned-ips.json")

            if os.path.exists(final_path):
                with open(final_path, "r") as f:
                    try:
                        file = json.load(f)
                    except json.decoder.JSONDecodeError:
                        file = []

                    for user in file:

                        valid_ip = False
                        checked_ip = user['ip']

                        # IP rule determination logic
                        for rule in original_ip_rules:
                            rule = rule.rule

                            # Allow singular IP if it's not also whitelisted
                            if rule.replace("!w", "") != checked_ip:
                                valid_ip = True

                            # Allow singular IP if it's not already in an IP range
                            if "/" in rule:
                                valid_ip = not in_subnet(checked_ip, rule.replace("!w", ""))
                                if not valid_ip:
                                    break

                        if valid_ip:
                            acl_object = check_global_acl(
                                global_acl,
                                AclRule(rule=user['ip'], acl_group='subnets')
                            )

                            acl_object.extra_data['created'] = user['created']
                            acl_object.extra_data['source'] = user['source']
                            acl_object.extra_data['expires'] = user['expires']
                            acl_object.extra_data['reason'] = user['reason']

                            server_acl['subnets'].append(acl_object)

            if list_type == "subnets":
                finalize()
                return server_acl['subnets']

    # Return entire list if list_type is unspecified ---------------------------------------------------------------
    if not list_type:
        finalize()
        return server_acl


# op_player("BlUe_KAZoo, kchicken, test")
# "Rule1, Rule2" --> [AclObject1, AclObject2]
# Returns: op_list
def op_user(server_name: str, rule_list: str or list, remove=False, force_version=None, write_file=True, temp_server=False):

    server_properties = dump_config(server_name)
    server_name = server_properties['name']
    version = server_properties['version']
    server_path = constants.tmpsvr if temp_server else server_properties['path']

    if force_version:
        version = force_version

    global_acl = load_global_acl()

    op_list = load_acl(server_name, "ops", force_version=version, temp_server=temp_server)
    name_list = [rule.rule.lower() for rule in op_list]

    if isinstance(rule_list, str):
        new_rules = [rule.strip() for rule in rule_list.split(",")]
    else:
        new_rules = [rule.strip() for rule in rule_list]

    # Iterate over new_rules if they exist
    if new_rules:
        for user in new_rules:

            # Ignore IP addresses
            if user.count(".") < 3:

                # Remove users from op_list
                if remove:
                    for x, rule in enumerate(op_list, 0):
                        if user.lower() == op_list[x].rule.lower():
                            op_list.pop(x)
                            name_list.pop(x)

                            # If server is running, check if player is online and run a command
                            if server_name in constants.server_manager.running_servers:
                                server_obj = constants.server_manager.running_servers[server_name]
                                if server_obj.running:
                                    server_obj.silent_command(f'deop {user}', log=False)

                            break

                # Add users to op_list
                else:
                    if user.lower() not in name_list:
                        user = get_uuid(user)

                        acl_object = check_global_acl(
                            global_acl,
                            AclRule(rule=user['name'], acl_group='ops')
                        )

                        acl_object.extra_data['uuid'] = user['uuid']
                        acl_object.extra_data['level'] = 4
                        acl_object.extra_data['bypassesPlayerLimit'] = True

                        op_list.append(acl_object)
                        name_list.append(user['name'].lower())


                        # If server is running, check if player is online and run a command
                        if server_name in constants.server_manager.running_servers:
                            server_obj = constants.server_manager.running_servers[server_name]
                            if server_obj.running:
                                server_obj.silent_command(f'op {user["name"]}', log=False)

        if write_file:

            # Edit old .txt files
            if constants.version_check(version, "<", constants.json_format_floor):
                final_list = ""

                # write final_list to file
                for user in op_list:
                    if user.rule:
                        final_list = final_list + user.rule + "\n"

                with open(os.path.join(server_path, "ops.txt"), "w+") as f:
                    f.write(final_list.lower())


            # Edit new .json files
            else:
                final_list = []

                # write new users to file
                for user in op_list:

                    op_uuid = user.extra_data['uuid']
                    op_name = user.rule

                    if op_name or op_uuid:

                        player = {
                            "uuid": f"{op_uuid}",
                            "name": f"{op_name}",
                            "level": int(user.extra_data['level']),
                            "bypassesPlayerLimit": bool(user.extra_data['bypassesPlayerLimit'])
                        }
                        final_list.append(player)

                    else:
                        continue

                with open(os.path.join(server_path, "ops.json"), "w+") as f:
                    f.write(json.dumps(final_list, indent=2))

    concat_db()
    return op_list


# ban_player("KChicken, 192.168.1.2, 192.168.0.0/24, !w 192.168.0.69, !w 192.168.0.128/28, 10.1.1.0-37")
# "Rule1, Rule2" --> [AclObject1, AclObject2]
# Returns: ban_list, subnet_list
def ban_user(server_name: str, rule_list: str or list, remove=False, force_version=None, write_file=True, temp_server=False, reason=None, length='forever'):

    server_properties = dump_config(server_name)
    server_name = server_properties['name']
    version = server_properties['version']
    server_path = constants.tmpsvr if temp_server else server_properties['path']

    if force_version:
        version = force_version

    global_acl = load_global_acl()

    ban_list = load_acl(server_name, "bans", force_version=version, temp_server=temp_server)
    name_list = [rule.rule.lower() for rule in ban_list]

    subnet_list = load_acl(server_name, "subnets", force_version=version, temp_server=temp_server)
    ip_list = [rule.rule.lower().replace(" ", "").strip() for rule in subnet_list]

    if isinstance(rule_list, str):
        new_rules = [rule.strip() for rule in rule_list.split(",")]
    else:
        new_rules = [rule.strip() for rule in rule_list]
    date = dt.now().strftime("%Y-%m-%d %H:%M:%S +0000")


    # Parse length parameter
    if length != 'forever':
        try:
            # Extract number and text from the input
            number = float(re.sub(r'[^0-9.]', '', length).strip())
            text = str(re.sub(r'[^a-zA-Z]', '', length).strip().lower())
            delta = None

            # Current time
            now = dt.now()

            # Seconds
            if text.startswith('s'):
                delta = timedelta(seconds=number)

            # Minutes
            elif text.startswith('m') and 'mo' not in text:
                delta = timedelta(minutes=number)

            # Hours
            elif text.startswith('h'):
                delta = timedelta(hours=number)

            # Days
            elif text.startswith('d'):
                delta = timedelta(days=number)

            # Weeks
            elif text.startswith('w'):
                delta = timedelta(weeks=number)

            # Months
            elif text.startswith('mo'):
                delta = relativedelta(months=int(number))

            # Years
            elif text.startswith('y'):
                delta = relativedelta(years=int(number))

            else:
                length = "forever"

            # Calculate future date
            if delta:
                future_date = now + delta

                # Convert to desired format: YYYY-MM-DD HH:MM:SS +TZ
                length = future_date.strftime('%Y-%m-%d %H:%M:%S %z')

        except (TypeError, ValueError) as e:
            length = 'forever'


    # Iterate over new_rules if they exist
    if new_rules:
        for user in new_rules:

            # If rule is a player
            if user.count(".") < 3:

                # Remove users from ban_list
                if remove:
                    for x, rule in enumerate(ban_list, 0):
                        if user.lower() == ban_list[x].rule.lower():
                            ban_list.pop(x)
                            name_list.pop(x)

                            # If server is running, check if player is online and run a command
                            if server_name in constants.server_manager.running_servers:
                                server_obj = constants.server_manager.running_servers[server_name]
                                if server_obj.running:
                                    server_obj.silent_command(f'pardon {user}', log=False)

                            break

                # Add users to ban_list
                else:
                    if user.lower() not in name_list:

                        user = get_uuid(user)

                        acl_object = check_global_acl(
                            global_acl,
                            AclRule(rule=user['name'], acl_group='bans')
                        )

                        try:
                            acl_object.extra_data['uuid'] = user['uuid']
                            acl_object.extra_data['created'] = user['created']
                            acl_object.extra_data['source'] = user['source']
                            acl_object.extra_data['expires'] = user['expires']
                            acl_object.extra_data['reason'] = user['reason']
                        except KeyError:
                            acl_object.extra_data['uuid'] = user['uuid']
                            acl_object.extra_data['created'] = date
                            acl_object.extra_data['source'] = "Server"
                            acl_object.extra_data['expires'] = length
                            acl_object.extra_data['reason'] = reason if reason else "Banned by an operator."

                        ban_list.append(acl_object)
                        name_list.append(user['name'].lower())

                        # If server is running, check if player is online and run a command
                        if server_name in constants.server_manager.running_servers:
                            server_obj = constants.server_manager.running_servers[server_name]
                            if server_obj.running:
                                server_obj.silent_command(f'ban {user["name"]} {reason}', log=False)


            # If rule is an IP or a subnet
            else:
                user = user.replace(" ", "")
                valid_ip = False

                # Subnet input validation
                if "-" in user:
                    if "!w" in user:
                        user = "!w" + str(min_network(user.replace("!w", "").strip()))
                    else:
                        user = str(min_network(user.strip()))

                if user == 'None' or not user:
                    continue

                if "/" in user:

                    # Whitelisted subnet
                    if "!w" in user:
                        user = user.replace("!w", "").strip()
                        if constants.check_subnet(user):
                            user = "!w" + str(ipaddress.ip_network(user.lower(), strict=False))
                            valid_ip = True

                    # Normal subnet
                    else:
                        # Possibly logic to simplify repetitive subnets
                        # already_included = any(
                        #     [
                        #         (
                        #             ipaddress.IPv4Network(sn.rule.replace("!w", "")).broadcast_address in ipaddress.ip_network(user.replace("!w", "")) and
                        #             ipaddress.IPv4Network(sn.rule.replace("!w", "")).network_address in ipaddress.ip_network(user.replace("!w", ""))
                        #         )
                        #         for sn in subnet_list if "/" in sn.rule
                        #     ]
                        # )
                        #
                        # print(already_included, print(user))

                        user = user.replace("!w", "").strip()
                        if constants.check_subnet(user):
                            user = str(ipaddress.ip_network(user.lower(), strict=False))
                            valid_ip = True


                # IP input validation
                else:
                    # Whitelisted IP
                    if "!w" in user:
                        user = user.replace("!w", "").strip()
                        if constants.check_ip(user):
                            user = "!w" + user.lower()
                            valid_ip = True

                    # Normal IP
                    else:
                        already_included = any(
                            [
                                (ipaddress.IPv4Address(user) in ipaddress.IPv4Network(sn.rule.replace("!w", "")))
                                for sn in subnet_list if "/" in sn.rule
                            ]
                        )
                        user = user.replace("!w", "").strip()
                        if constants.check_ip(user) and not already_included:
                            valid_ip = True

                if not valid_ip:
                    continue

                # Remove IPs from subnet_list
                if remove:
                    for x, rule in enumerate(subnet_list, 0):
                        if user.lower() == subnet_list[x].rule.lower():
                            subnet_list.pop(x)
                            ip_list.pop(x)

                            # If server is running, check if player is online and run a command
                            if server_name in constants.server_manager.running_servers:
                                server_obj = constants.server_manager.running_servers[server_name]
                                if server_obj.running:
                                    server_obj.silent_command(f'pardon-ip {user}', log=False)

                            break

                # Add IPs to subnet_list
                else:
                    if user.lower() not in ip_list and valid_ip:
                        acl_object = check_global_acl(
                            global_acl,
                            AclRule(rule=user.lower(), acl_group='subnets')
                        )

                        acl_object.extra_data['created'] = date
                        acl_object.extra_data['source'] = "Server"
                        acl_object.extra_data['expires'] = length
                        acl_object.extra_data['reason'] = reason if reason else "Banned by an operator."

                        subnet_list.append(acl_object)
                        ip_list.append(user.lower())

                        # If server is running, check if player is online and run a command
                        if server_name in constants.server_manager.running_servers:
                            server_obj = constants.server_manager.running_servers[server_name]
                            if server_obj.running:
                                server_obj.silent_command(f'ban-ip {user}{reason}', log=False)


        if write_file:

            # Edit old .txt files
            if constants.version_check(version, "<", constants.json_format_floor):

                # Add banned users ---------------------------------------------------------------------------------
                final_list = ""

                # write final_list to file
                for user in ban_list:
                    if user.rule:
                        final_list = final_list + user.rule + "\n"

                with open(os.path.join(server_path, "banned-players.txt"), "w+") as f:
                    f.write(final_list.lower())

                # Add banned IPs -----------------------------------------------------------------------------------
                final_list = ""

                # write final_list to file
                for ip_addr in gen_iplist(subnet_list):
                    if ip_addr:
                        final_list = final_list + ip_addr + "\n"

                with open(os.path.join(server_path, "banned-ips.txt"), "w+") as f:
                    f.write(final_list.lower())


            # Edit new .json files
            else:

                # Add banned users ---------------------------------------------------------------------------------
                final_list = []

                # write new users to file
                for user in ban_list:

                    ban_uuid = user.extra_data['uuid']
                    ban_name = user.rule

                    if ban_name or ban_uuid:

                        player = {
                            "uuid": f"{ban_uuid}",
                            "name": f"{ban_name}",
                            "created": f"{user.extra_data['created']}",
                            "source": f"{user.extra_data['source']}",
                            "expires": f"{user.extra_data['expires']}",
                            "reason": f"{user.extra_data['reason']}"
                        }

                        final_list.append(player)

                    else:
                        continue

                with open(os.path.join(server_path, "banned-players.json"), "w+") as f:
                    f.write(json.dumps(final_list, indent=2))

                # Add banned IPs -----------------------------------------------------------------------------------
                final_list = []

                # write new users to file
                for ip_addr in gen_iplist(subnet_list):

                    if ip_addr:

                        if isinstance(ip_addr, str):

                            ip = {
                                "ip": f"{ip_addr}",
                                "created": f"{date}",
                                "source": f"Server",
                                "expires": f"forever",
                                "reason": f"Banned by an operator."
                            }

                        else:

                            ip = {
                                "ip": f"{ip_addr.rule}",
                                "created": f"{ip_addr.extra_data['created']}",
                                "source": f"{ip_addr.extra_data['source']}",
                                "expires": f"{ip_addr.extra_data['expires']}",
                                "reason": f"{ip_addr.extra_data['reason']}"
                            }

                        final_list.append(ip)

                    else:
                        continue

                with open(os.path.join(server_path, "banned-ips.json"), "w+") as f:
                    f.write(json.dumps(final_list, indent=2))

            # Write subnet rules to file
            with open(os.path.join(server_path, "banned-subnets.json"), "w+") as f:
                f.write(json.dumps([rule.rule for rule in subnet_list], indent=2))

    concat_db()
    return ban_list, subnet_list


# whitelist_player("BlUe_KAZoo, kchicken, test")
# "Rule1, Rule2" --> [AclObject1, AclObject2]
# Returns: wl_list, op_list
def wl_user(server_name: str, rule_list: str or list, remove=False, force_version=None, write_file=True, temp_server=False):

    server_properties = dump_config(server_name)
    server_name = server_properties['name']
    version = server_properties['version']
    server_path = constants.tmpsvr if temp_server else server_properties['path']

    if force_version:
        version = force_version

    global_acl = load_global_acl()

    wl_list = load_acl(server_name, "wl", force_version=version, temp_server=temp_server)
    name_list = [rule.rule.lower() for rule in wl_list]

    if isinstance(rule_list, str):
        new_rules = [rule.strip() for rule in rule_list.split(",")]
    else:
        new_rules = [rule.strip() for rule in rule_list]

    op_list = []
    new_op_list = []
    if remove:
        op_list = [rule.rule.lower() for rule in load_acl(server_name, "ops", force_version=version)]

    # Iterate over new_rules if they exist
    if new_rules:
        for user in new_rules:

            # Ignore IP addresses
            if user.count(".") < 3:

                # Remove users from wl_list
                if remove:

                    # Remove OP status if whitelist removed so the user can't connect
                    if user.lower() in op_list:
                        new_op_list = op_user(server_name, user, remove=True, force_version=version)

                    for x, rule in enumerate(wl_list, 0):
                        if user.lower() == wl_list[x].rule.lower():
                            wl_list.pop(x)
                            name_list.pop(x)

                            # If server is running, check if player is online and run a command
                            if server_name in constants.server_manager.running_servers:
                                server_obj = constants.server_manager.running_servers[server_name]
                                if server_obj.running:
                                    server_obj.silent_command(f'whitelist remove {user}', log=False)
                                    server_obj.silent_command(f'whitelist reload', log=False)
                                    if server_obj.acl.server['whitelist']:
                                        server_obj.silent_command(f'kick {user} You are not whitelisted on this server!', log=False)

                            break

                # Add users to wl_list
                else:
                    if user.lower() not in name_list:
                        user = get_uuid(user)

                        acl_object = check_global_acl(
                            global_acl,
                            AclRule(rule=user['name'], acl_group='wl')
                        )

                        acl_object.extra_data['uuid'] = user['uuid']

                        wl_list.append(acl_object)
                        name_list.append(user['name'].lower())


                        # If server is running, check if player is online and run a command
                        if server_name in constants.server_manager.running_servers:
                            server_obj = constants.server_manager.running_servers[server_name]
                            if server_obj.running:
                                server_obj.silent_command(f'whitelist add {user["name"]}', log=False)
                                server_obj.silent_command(f'whitelist reload', log=False)

        if write_file:

            # Edit old .txt files
            if constants.version_check(version, "<", constants.json_format_floor):
                final_list = ""

                # write final_list to file
                for user in wl_list:
                    if user.rule:
                        final_list = final_list + user.rule + "\n"

                with open(os.path.join(server_path, "white-list.txt"), "w+") as f:
                    f.write(final_list.lower())


            # Edit new .json files
            else:
                final_list = []

                # write new users to file
                for user in wl_list:

                    wl_uuid = user.extra_data['uuid']
                    wl_name = user.rule

                    if wl_name or wl_uuid:

                        player = {
                            "uuid": f"{wl_uuid}",
                            "name": f"{wl_name}",
                        }
                        final_list.append(player)

                    else:
                        continue

                with open(os.path.join(server_path, "whitelist.json"), "w+") as f:
                    f.write(json.dumps(final_list, indent=2))

    concat_db()
    return wl_list, new_op_list


# Converts PlayerScriptObject or list of PlayerScriptObjects to str
def convert_obj_to_str(rule_list: str or list or PlayerScriptObject):
    if isinstance(rule_list, list):
        if isinstance(rule_list[0], PlayerScriptObject):
            rule_list = [p.name for p in rule_list]
    elif isinstance(rule_list, PlayerScriptObject):
        rule_list = rule_list.name
    return rule_list


# ---------------------------------------------- Usage Examples --------------------------------------------------------

#   ops:
#       server operators
#
#   bans:
#       banned players
#
#   wl:
#       whitelisted players
#
#   subnets:
#       banned IPs, banned IP ranges, and whitelisted IPs in ban ranges
#
#
#   Access list priority:
#
#   whitelist --> operator --> ban
#   IP address --> IP range --> IP whitelist



# properties = {"name": "1.17.1 Server", "type": "vanilla", "version": "1.17.1"}

# # Load current ACL:
# acl = AclManager(properties['name'])

# # Edit ACL:
# acl.get_rule("127.0.0.1")
# acl._process_query("!g KChicken, !w 192.168.1.2", list_type="bans")
# acl.op_player("ChaffyCosine669, blue_kazoo", remove=False)
# acl.whitelist_player("test1, test2, test3", remove=False)
# acl.ban_player("KChicken, 192.168.1.2, 192.168.0.0/24, !w 192.168.0.69, !w 192.168.0.128/28, 10.1.1.10-37")
# acl.add_global_rule("KChicken, blue_kazoo", list_type="ops", remove=False)

# # If ACL is a new server
# acl.write_rules()
