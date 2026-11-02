"""auto-mcs ACL regression and compatibility tests (dev and acl-fixes).

COPY TO: <repo>/tests/test_acl_regression.py
RUN:     python -m unittest discover -s tests -p test_acl_regression.py -v
OR:      python tests/test_acl_regression.py --source /path/to/other/checkout/source/core/server/acl.py

Only reads the source file from the checkout. All cache, config, server, and
Minecraft ACL files are created under TemporaryDirectory; no user data is
modified and no real network traffic / Minecraft commands are sent.

The suite compiles the EXACT top-level classes/functions from acl.py via AST,
while replacing unrelated application services with deterministic fixtures.
This avoids importing Kivy/auto-mcs or needing production account/config data.
It does NOT validate Minecraft itself, its migration on first boot, GUI widgets,
or real Telepath transport. Dev may fail assertions documenting existing bugs.
"""
from __future__ import annotations

import argparse
import ast
import copy
import datetime
import glob
import inspect
import ipaddress
import json
import os
import pathlib
import re
import shutil
import tempfile
import threading
import time
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime as dt, timedelta
from functools import partial
from unittest import mock

DEFAULT_SOURCE = pathlib.Path(__file__).resolve().parents[1] / 'source/core/server/acl.py'
SOURCE = pathlib.Path(os.environ.get('ACL_TEST_SOURCE', str(DEFAULT_SOURCE))).expanduser().resolve()
PLAYER_UUIDS = {
    'Alice': 'a' * 32,
    'Bob': 'b' * 32,
    'Charlie': 'c' * 32,
    'Dave': 'd' * 32,
    'OldName': 'e' * 32,
    'NewName': 'e' * 32,
    'Other': 'f' * 32,
}


def canonical_uuid(value):
    return str(value or '').replace('-', '').lower()


def names(records):
    return [v.rule if hasattr(v, 'rule') else v.get('name') for v in records]


class FakeHTTPResponse:
    status_code = 200

    def __init__(self, uuid, name):
        self.uuid, self.name = uuid, name

    def json(self):
        return {'code': 'player.found', 'data': {'player': {'id': self.uuid, 'username': self.name}}}


class DummyTimer:
    def __init__(self, delay, callback, *args, **kwargs):
        self.callback, self.args, self.kwargs = callback, args, kwargs

    def start(self):
        # Explicitly invoked by tests, rather than spawning uncontrolled timers.
        return self

    def fire(self):
        return self.callback(*self.args, **self.kwargs)


class FakeServer:
    def __init__(self, name='A'):
        self.name = name
        self.running = True
        self.commands = []
        self.messages = []
        self.acl = types.SimpleNamespace(server={'whitelist': True}, reload_list=lambda group=None: None)

    def silent_command(self, command, **kwargs):
        self.commands.append(command)

    def send_log(self, message, level=None):
        self.messages.append((message, level))


class FakeServerManager:
    def __init__(self, fixture):
        self.fixture = fixture
        self.running_servers = {}

    def create_server_list(self):
        return list(self.fixture.servers)


class Sandbox:
    """Compiles real acl.py nodes into an isolated namespace with fake services."""

    NODES = {
        'AclRule', 'AclManager', 'convert_obj_to_str', 'in_subnet', 'count_subnet',
        'min_network', 'gen_iplist', 'load_global_acl', 'check_global_acl',
        '_write_acl_file', '_write_acl_list', 'migrate_acl', '_find_acl_rule',
        'add_global_rule', 'stage_uuid', 'get_uuid', 'load_uuid_db', 'concat_db',
        'load_acl', 'op_user', 'ban_user', 'wl_user', '_apply_runtime_ip_rule',
        '_resolve_acl_user',
    }

    def __init__(self):
        if not SOURCE.is_file():
            raise FileNotFoundError(
                f'ACL source not found: {SOURCE}\n'
                'Place this file inside <repo>/tests/ or pass --source /path/to/acl.py.'
            )
        self.tmp = tempfile.TemporaryDirectory(prefix='auto-mcs-acl-regression-')
        self.root = pathlib.Path(self.tmp.name)
        self.cache = self.root / 'cache'
        self.cache.mkdir()
        self.config = self.root / 'config'
        self.config.mkdir()
        self.temp_server = self.root / 'temporary-server'
        self.temp_server.mkdir()
        self.servers = {}
        self.logs = []
        self.http_calls = []
        self.timers = []
        self.http_names = dict(PLAYER_UUIDS)
        self.app_online = False
        self.server_manager = FakeServerManager(self)
        self.namespace = self._compile()
        self.global_path = self.config / 'global-acl.json'
        self.uuid_path = self.cache / 'uuid-db.json'
        self.uuid_path.write_text('[]', encoding='utf-8')
        self.write_global()
        self.add_server('A')

    def close(self):
        self.tmp.cleanup()

    @property
    def feature_stage(self):
        return 'stage_uuid' in self.namespace

    @property
    def feature_rename(self):
        return 'rename' in inspect.signature(self.fn('add_global_rule')).parameters

    @staticmethod
    def version_check(version, comparison, boundary):
        def num(s):
            # Covers the concrete test versions 1.6.4, 1.7.5, 1.7.6, 1.8, 1.20.1.
            values = re.findall(r'\d+', str(s))
            return tuple(int(n) for n in values[:3]) + (0,) * max(0, 3 - len(values[:3]))
        a, b = num(version), num(boundary)
        return {'<': a < b, '<=': a <= b, '>': a > b, '>=': a >= b, '==': a == b}[comparison]

    @staticmethod
    def check_ip(value, *args):
        try:
            return isinstance(ipaddress.ip_address(str(value).replace('!w', '')), ipaddress.IPv4Address)
        except ValueError:
            return False

    @staticmethod
    def check_subnet(value):
        try:
            return isinstance(ipaddress.ip_network(str(value).replace('!w', ''), strict=False), ipaddress.IPv4Network)
        except ValueError:
            return False

    def get_url(self, url, **kwargs):
        self.http_calls.append(url)
        identifier = url.rsplit('/', 1)[-1]
        matches = [(name, uuid) for name, uuid in self.http_names.items()
                   if identifier.casefold() == name.casefold() or canonical_uuid(identifier) == uuid]
        if not matches:
            return types.SimpleNamespace(status_code=404, json=lambda: {'code': 'player.not_found'})
        # Favor the canonical current username for renamed UUIDs.
        name, uuid = matches[-1] if canonical_uuid(identifier) == PLAYER_UUIDS['NewName'] else matches[0]
        return FakeHTTPResponse(uuid, name)

    def _compile(self):
        source = SOURCE.read_text(encoding='utf-8')
        tree = ast.parse(source, filename=str(SOURCE))
        found = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                 and node.name in self.NODES}
        missing = {'AclRule', 'AclManager', 'load_acl', 'load_uuid_db', 'get_uuid', 'concat_db',
                   'ban_user', 'op_user', 'wl_user', 'gen_iplist', 'load_global_acl'} - found.keys()
        if missing:
            raise RuntimeError(f'{SOURCE} missing expected functions/classes: {sorted(missing)}')

        try:
            from dateutil.relativedelta import relativedelta
        except ImportError:
            # Only needed for month/year duration parsing; all other tests run stdlib-only.
            relativedelta = None

        constants = types.SimpleNamespace(
            app_online=False,
            app_config=types.SimpleNamespace(enable_ip_lookup=False),
            json_format_floor='1.7.6',
            server_ini='auto-mcs.ini',
            server_manager=self.server_manager,
            folder_check=lambda p: pathlib.Path(p).mkdir(parents=True, exist_ok=True),
            format_traceback=lambda e: f'{type(e).__name__}: {e}',
            version_check=self.version_check,
            check_ip=self.check_ip,
            check_subnet=self.check_subnet,
            get_url=self.get_url,
            safe_delete=lambda p: shutil.rmtree(p, ignore_errors=True),
        )
        paths = types.SimpleNamespace(cache=str(self.cache), config=str(self.config), tmpsvr=str(self.temp_server))

        class FakeManager:
            @staticmethod
            def server_path(name, filename=None):
                srv = self.servers.get(name)
                if srv is None or srv['new']:
                    return None
                path = srv['path'] / filename if filename else srv['path']
                return str(path) if path.exists() else None

        def make_timer(*args, **kwargs):
            timer = DummyTimer(*args, **kwargs)
            self.timers.append(timer)
            return timer

        def dump_config(name, new_server=False):
            server = self.servers[name]
            return {'name': name, 'version': server['version'], 'path': str(server['path']),
                    'world': 'world', 'whitelist': server['whitelist']}

        ns = {
            '__name__': 'isolated_auto_mcs_acl', '__file__': str(SOURCE),
            'os': os, 'json': json, 'glob': glob.glob, 're': re, 'copy2': shutil.copy2,
            'deepcopy': copy.deepcopy, 'ipaddress': ipaddress, 'tempfile': tempfile,
            'ThreadPoolExecutor': ThreadPoolExecutor, 'Lock': threading.Lock, 'RLock': threading.RLock,
            'dt': dt, 'timedelta': timedelta, 'relativedelta': relativedelta,
            'time': time, 'socket': __import__('socket'), 'urlopen': lambda *a, **k: None,
            'constants': constants, 'paths': paths, 'cache_folder': str(self.cache),
            'uuid_db': str(self.cache / 'uuid-db.json'),
            'global_acl_file': str(self.config / 'global-acl.json'),
            'uuid_db_lock': threading.Lock(), 'global_acl_lock': threading.RLock(),
            'json_repair': types.SimpleNamespace(loads=json.loads),
            'send_log': lambda source, message, level=None: self.logs.append((source, str(message), level)),
            'manager': FakeManager, 'dump_config': dump_config,
            'dTimer': make_timer, 'PlayerScriptObject': type('PlayerScriptObject', (), {}),
            'translate': lambda x: x, 'in_subnet': lambda addr, cidr: ipaddress.ip_address(addr) in ipaddress.ip_network(cidr),
        }
        # Future-annotations allows compiling the production classes without importing
        # types used only in hints. No behavior or source is rewritten.
        future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
        selected = [future] + [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                                and node.name in found]
        exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])), str(SOURCE), 'exec'), ns)
        return ns

    def fn(self, name):
        return self.namespace[name]

    def add_server(self, name, version='1.20.1', new=False, whitelist=False):
        path = self.root / name
        path.mkdir(exist_ok=True)
        (path / 'world').mkdir(exist_ok=True)
        self.servers[name] = {'path': path, 'version': version, 'new': new, 'whitelist': whitelist}
        if not new:
            (path / 'auto-mcs.ini').write_text('test fixture', encoding='utf-8')
        return path

    def write_global(self, **groups):
        data = {'ops': [], 'bans': [], 'wl': [], 'subnets': []}
        data.update(groups)
        self.global_path.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def read_global(self):
        return json.loads(self.global_path.read_text(encoding='utf-8'))

    def seed_uuid(self, **players):
        records = [{'uuid': PLAYER_UUIDS.get(name, '9' * 32), 'name': name} for name in players]
        records = [{**r, **(players[r['name']] or {})} for r in records]
        self.uuid_path.write_text(json.dumps(records, indent=2), encoding='utf-8')

    def db(self):
        return json.loads(self.uuid_path.read_text(encoding='utf-8'))

    def server_file(self, name, filename, content):
        path = self.servers[name]['path'] / filename
        if isinstance(content, (list, dict)):
            path.write_text(json.dumps(content, indent=2), encoding='utf-8')
        else:
            path.write_text(content, encoding='utf-8')
        return path

    def read_file(self, name, filename):
        path = self.servers[name]['path'] / filename
        return json.loads(path.read_text(encoding='utf-8'))

    def user(self, name):
        return {'uuid': PLAYER_UUIDS[name], 'name': name}

    def op(self, name, **changes):
        return {**self.user(name), 'level': 4, 'bypassesPlayerLimit': True, **changes}

    def ban(self, name, **changes):
        return {**self.user(name), 'created': '2024-01-02 03:04:05 +0000',
                'source': 'Server', 'expires': 'forever', 'reason': 'Original reason', **changes}

    def ipban(self, ip, **changes):
        return {'ip': ip, 'created': '2024-01-02 03:04:05 +0000',
                'source': 'Server', 'expires': 'forever', 'reason': 'Original reason', **changes}

    def ensure_modern_files(self, server='A'):
        for filename in ('ops.json', 'banned-players.json', 'whitelist.json', 'banned-ips.json', 'banned-subnets.json'):
            path = self.servers[server]['path'] / filename
            if not path.exists():
                path.write_text('[]', encoding='utf-8')

    def call(self, function, *args, **kwargs):
        """Pass only supported keyword args; supports both dev and acl-fixes."""
        fn = self.fn(function)
        params = inspect.signature(fn).parameters
        return fn(*args, **{k: v for k, v in kwargs.items() if k in params})

    def set_online(self, online=True):
        self.namespace['constants'].app_online = online

    def manager(self, name='A'):
        return self.fn('AclManager')(name)

    def running(self, name='A'):
        obj = FakeServer(name)
        self.server_manager.running_servers[name] = obj
        return obj


class ACLTestCase(unittest.TestCase):
    def setUp(self):
        self.s = Sandbox()
        self.s.ensure_modern_files()
        self.s.seed_uuid(Alice={}, Bob={}, Charlie={}, Dave={}, OldName={})

    def tearDown(self):
        self.s.close()

    def rules(self, group, server='A', **kwargs):
        return self.s.call('load_acl', server, group, **kwargs)

    def assert_names(self, items, expected):
        self.assertCountEqual(names(items), expected)

    def require_current(self, feature='stage_uuid'):
        if feature not in self.s.namespace:
            self.skipTest(f'{feature} is absent on dev; current-branch-only behavior')

    def stage(self, name='Alice', **metadata):
        self.require_current()
        return self.s.call('stage_uuid', {**self.s.user(name), **metadata}, source='login')


class TestSubnetExpansion(ACLTestCase):
    """Directly exercises the real gen_iplist / ban_user / load_acl algorithms."""

    def expand(self, *inputs):
        R = self.s.fn('AclRule')
        return self.s.fn('gen_iplist')([R(rule=x, acl_group='subnets') for x in inputs])

    def test_single_ipv4_and_duplicates(self):
        self.assertCountEqual(self.expand('192.168.12.4', '192.168.12.4'), ['192.168.12.4'])

    def test_small_subnet_excludes_network_and_broadcast(self):
        self.assertCountEqual(self.expand('192.168.12.0/29'),
                              [f'192.168.12.{i}' for i in range(1, 7)])

    def test_slash_30_and_29_and_28_cardinality(self):
        for cidr, expected in [(30, 2), (29, 6), (28, 14)]:
            with self.subTest(prefix=cidr):
                self.assertEqual(len(set(self.expand(f'10.90.0.0/{cidr}'))), expected)

    def test_slash_31_and_32_boundaries(self):
        # Correct CIDR semantics: both /31 addresses and the single /32 host
        # must be banned. Currently these assertions detect a production bug.
        self.assertCountEqual(self.expand('10.0.0.0/31'), ['10.0.0.0', '10.0.0.1'])
        self.assertEqual(self.expand('10.0.0.1/32'), ['10.0.0.1'])

    def test_whitelisted_single_ip_punches_hole(self):
        self.assertCountEqual(self.expand('10.20.30.0/29', '!w10.20.30.3'),
                              [f'10.20.30.{i}' for i in (1, 2, 4, 5, 6)])

    def test_whitelisted_subnet_punches_hole(self):
        self.assertCountEqual(self.expand('10.20.30.0/28', '!w10.20.30.8/30'),
                              [f'10.20.30.{i}' for i in range(1, 15) if i not in (9, 10)])

    def test_whitelist_entire_subnet(self):
        self.assertEqual(self.expand('10.20.30.0/29', '!w10.20.30.0/29'), [])

    def test_whitelist_outside_subnet_no_effect(self):
        self.assertCountEqual(self.expand('10.20.30.0/29', '!w10.20.99.2'),
                              [f'10.20.30.{i}' for i in range(1, 7)])

    def test_whitelist_with_standalone_ban(self):
        self.assertCountEqual(self.expand('10.20.30.3', '!w10.20.30.3'), [])

    def test_multiple_overlapping_ranges_no_duplicate_addresses(self):
        iplist = self.expand('10.20.30.0/29', '10.20.30.0/30')
        self.assertEqual(len(iplist), len(set(iplist)))
        self.assertCountEqual(iplist, [f'10.20.30.{i}' for i in range(1, 7)])

    def test_exact_ip_and_covering_range_no_duplicate_addresses(self):
        iplist = self.expand('10.20.30.0/29', '10.20.30.3')
        self.assertEqual(len(iplist), len(set(iplist)))
        self.assertCountEqual(iplist, [f'10.20.30.{i}' for i in range(1, 7)])

    def test_multiple_whitelists_together(self):
        self.assertCountEqual(self.expand('10.20.30.0/28', '!w10.20.30.2', '!w10.20.30.8/30'),
                              [f'10.20.30.{i}' for i in range(1, 15) if i not in (2, 9, 10)])

    def test_range_normalization(self):
        self.assertEqual(self.s.fn('min_network')('10.1.1.4-7'), '10.1.1.4/30')
        self.assertEqual(self.s.fn('min_network')('10.1.1.4-10'), '10.1.1.0/28')

    def test_malformed_range_is_not_accepted(self):
        self.assertIsNone(self.s.fn('min_network')('10.1.1.500-501'))

    def test_subnet_rule_persists_and_expands(self):
        self.s.call('ban_user', 'A', '10.20.30.0/29', reason='CIDR test')
        self.assertIn('10.20.30.0/29', self.s.read_file('A', 'banned-subnets.json'))
        self.assertCountEqual([x['ip'] for x in self.s.read_file('A', 'banned-ips.json')],
                              [f'10.20.30.{i}' for i in range(1, 7)])

    def test_whitelisted_hole_persists_and_expands(self):
        self.s.call('ban_user', 'A', '10.20.30.0/29')
        self.s.call('ban_user', 'A', '!w10.20.30.3')
        self.assertIn('!w10.20.30.3', self.s.read_file('A', 'banned-subnets.json'))
        self.assertNotIn('10.20.30.3', [x['ip'] for x in self.s.read_file('A', 'banned-ips.json')])

    def test_remove_whitelist_reinstates_banned_ip(self):
        self.s.call('ban_user', 'A', '10.20.30.0/29, !w10.20.30.3')
        self.s.call('ban_user', 'A', '!w10.20.30.3', remove=True)
        self.assertIn('10.20.30.3', [x['ip'] for x in self.s.read_file('A', 'banned-ips.json')])

    def test_remove_subnet_clears_expansion(self):
        self.s.call('ban_user', 'A', '10.20.30.0/29')
        self.s.call('ban_user', 'A', '10.20.30.0/29', remove=True)
        self.assertNotIn('10.20.30.0/29', self.s.read_file('A', 'banned-subnets.json'))
        self.assertNotIn('10.20.30.1', [x['ip'] for x in self.s.read_file('A', 'banned-ips.json')])

    def test_subnet_normalization_input(self):
        self.s.call('ban_user', 'A', '10.20.30.5/29')
        self.assertIn('10.20.30.0/29', self.s.read_file('A', 'banned-subnets.json'))

    def test_range_input_persisted_as_cidr(self):
        self.s.call('ban_user', 'A', '10.20.30.0-7')
        self.assertIn('10.20.30.0/29', self.s.read_file('A', 'banned-subnets.json'))

    def test_duplicate_subnet_add_is_idempotent(self):
        self.s.call('ban_user', 'A', '10.20.30.0/29')
        self.s.call('ban_user', 'A', '10.20.30.0/29')
        self.assertEqual(self.s.read_file('A', 'banned-subnets.json').count('10.20.30.0/29'), 1)

    def test_invalid_ip_and_cidr_do_not_enter_files(self):
        self.s.call('ban_user', 'A', '999.999.999.999, 10.20.30.999/29')
        self.assertEqual(self.s.read_file('A', 'banned-subnets.json'), [])

    def test_direct_ip_reason_preserved_on_rewrite(self):
        self.s.server_file('A', 'banned-subnets.json', ['10.20.30.3'])
        self.s.server_file('A', 'banned-ips.json', [self.s.ipban('10.20.30.3', reason='Do not erase')])
        self.s.call('ban_user', 'A', '10.20.30.5')
        match = [v for v in self.s.read_file('A', 'banned-ips.json') if v['ip'] == '10.20.30.3']
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]['reason'], 'Do not erase')

    def test_live_ip_commands_and_exclusions(self):
        running = self.s.running()
        self.s.call('ban_user', 'A', '10.20.30.3')
        self.assertIn('ban-ip 10.20.30.3', ' '.join(running.commands))
        running.commands.clear()
        self.s.call('ban_user', 'A', '!w10.20.30.3')
        self.assertFalse(any('ban-ip !w' in x for x in running.commands))
        self.s.call('ban_user', 'A', '10.20.30.3', remove=True)
        self.assertTrue(any('pardon-ip 10.20.30.3' in x for x in running.commands))

    def test_subnet_reload_restores_rules(self):
        self.s.server_file('A', 'banned-subnets.json', ['10.20.30.0/29', '!w10.20.30.3'])
        self.s.server_file('A', 'banned-ips.json', [self.s.ipban('10.20.30.1'), self.s.ipban('10.20.30.2')])
        self.assert_names(self.rules('subnets'), ['10.20.30.0/29', '!w10.20.30.3'])

    def test_standalone_ip_load_without_subnets(self):
        # Currently fails on both branches: valid_ip starts False and remains
        # False when original_ip_rules is empty. This is a deliberate detector.
        self.s.server_file('A', 'banned-subnets.json', [])
        self.s.server_file('A', 'banned-ips.json', [self.s.ipban('10.20.30.3')])
        self.assertIn('10.20.30.3', names(self.rules('subnets')))

    def test_subnet_rebuild_keeps_globally_managed_subnet(self):
        self.s.write_global(subnets=['10.20.30.0/29'])
        self.s.call('ban_user', 'A', '10.20.30.5')
        self.assertIn('10.20.30.0/29', self.s.read_file('A', 'banned-subnets.json'))


    def test_small_subnet_issues_live_commands_for_each_address(self):
        server = self.s.running()
        self.s.call('ban_user', 'A', '10.20.30.0/29', reason='live test')
        commands = [x for x in server.commands if x.startswith('ban-ip ')]
        self.assertEqual(len(commands), 6)
        self.assertTrue(any('10.20.30.1' in x for x in commands))
        self.assertTrue(any('10.20.30.6' in x for x in commands))

    def test_live_small_subnet_respects_existing_exclusion(self):
        server = self.s.running()
        self.s.call('ban_user', 'A', '!w10.20.30.3')
        server.commands.clear()
        self.s.call('ban_user', 'A', '10.20.30.0/29')
        commands = [x for x in server.commands if x.startswith('ban-ip ')]
        self.assertEqual(len(commands), 5)
        self.assertFalse(any('10.20.30.3' in x for x in commands))

    def test_large_subnet_deferred_live_and_written_on_disk(self):
        server = self.s.running()
        self.s.call('ban_user', 'A', '10.20.30.0/23')
        self.assertEqual([x for x in server.commands if x.startswith('ban-ip ')], [])
        self.assertTrue(any('restart' in msg.lower() for msg, _ in server.messages))
        self.assertIn('10.20.30.0/23', self.s.read_file('A', 'banned-subnets.json'))

    def test_cidr_remove_preserves_other_subnet(self):
        self.s.call('ban_user', 'A', '10.20.30.0/29, 10.20.31.0/29')
        self.s.call('ban_user', 'A', '10.20.30.0/29', remove=True)
        self.assertEqual(self.s.read_file('A', 'banned-subnets.json'), ['10.20.31.0/29'])
        self.assertCountEqual([x['ip'] for x in self.s.read_file('A', 'banned-ips.json')],
                              [f'10.20.31.{i}' for i in range(1, 7)])

    def test_whitelist_does_not_add_ban_when_no_range(self):
        self.s.call('ban_user', 'A', '!w10.20.30.3')
        self.assertIn('!w10.20.30.3', self.s.read_file('A', 'banned-subnets.json'))
        self.assertEqual(self.s.read_file('A', 'banned-ips.json'), [])

    def test_global_ip_remove_does_not_erase_local_ip(self):
        self.s.call('ban_user', 'A', '10.20.31.2')
        self.s.call('add_global_rule', '10.20.30.0/29', 'bans')
        self.s.call('add_global_rule', '10.20.30.0/29', 'bans', remove=True)
        self.assertIn('10.20.31.2', self.s.read_file('A', 'banned-subnets.json'))
        self.assertIn('10.20.31.2', [v['ip'] for v in self.s.read_file('A', 'banned-ips.json')])


class TestPlayerRules(ACLTestCase):
    def test_op_add_remove_persist(self):
        self.s.call('op_user', 'A', 'Alice')
        records = self.s.read_file('A', 'ops.json')
        self.assertEqual([(x['name'], x['uuid'], x['level']) for x in records], [('Alice', PLAYER_UUIDS['Alice'], 4)])
        self.s.call('op_user', 'A', 'Alice', remove=True)
        self.assertEqual(self.s.read_file('A', 'ops.json'), [])

    def test_op_multiple_add_and_no_duplicates(self):
        self.s.call('op_user', 'A', 'Alice, Bob, Charlie')
        self.s.call('op_user', 'A', 'Alice')
        self.assert_names(self.rules('ops'), ['Alice', 'Bob', 'Charlie'])

    def test_ban_add_remove_and_metadata(self):
        self.s.call('ban_user', 'A', 'Alice', reason='Regression check', length='forever')
        record = self.s.read_file('A', 'banned-players.json')[0]
        self.assertEqual((record['name'], record['reason'], record['expires']),
                         ('Alice', 'Regression check', 'forever'))
        self.s.call('ban_user', 'A', 'Alice', remove=True)
        self.assertEqual(self.s.read_file('A', 'banned-players.json'), [])

    def test_ban_custom_metadata_survives_unrelated_edit(self):
        existing = self.s.ban('Alice', reason='Important custom reason', expires='2032-02-02 00:00:00 +0000')
        self.s.server_file('A', 'banned-players.json', [existing])
        self.s.call('ban_user', 'A', 'Bob')
        record = next(x for x in self.s.read_file('A', 'banned-players.json') if x['name'] == 'Alice')
        self.assertEqual(record['reason'], existing['reason'])
        self.assertEqual(record['expires'], existing['expires'])

    def test_expiry_duration_units(self):
        for value in ('10s', '5m', '2h', '3d', '2w'):
            with self.subTest(length=value):
                self.s.server_file('A', 'banned-players.json', [])
                self.s.call('ban_user', 'A', 'Alice', length=value)
                self.assertNotEqual(self.s.read_file('A', 'banned-players.json')[0]['expires'], 'forever')

    def test_invalid_duration_defaults_forever(self):
        self.s.call('ban_user', 'A', 'Alice', length='not-a-duration')
        self.assertEqual(self.s.read_file('A', 'banned-players.json')[0]['expires'], 'forever')

    def test_whitelist_add_remove(self):
        self.s.call('wl_user', 'A', 'Alice, Bob')
        self.assert_names(self.rules('wl'), ['Alice', 'Bob'])
        self.s.call('wl_user', 'A', 'Alice', remove=True)
        self.assert_names(self.rules('wl'), ['Bob'])

    def test_whitelist_removal_deops_player(self):
        self.s.server_file('A', 'ops.json', [self.s.op('Alice')])
        self.s.server_file('A', 'whitelist.json', [self.s.user('Alice')])
        self.s.call('wl_user', 'A', 'Alice', remove=True)
        self.assertNotIn('Alice', [x['name'] for x in self.s.read_file('A', 'ops.json')])

    def test_bans_and_subnets_do_not_collide(self):
        self.s.call('ban_user', 'A', 'Alice, 10.20.30.0/29')
        self.assert_names(self.rules('bans'), ['Alice'])
        self.assertIn('10.20.30.0/29', names(self.rules('subnets')))

    def test_all_rule_types_and_scope(self):
        self.s.write_global(ops=[self.s.user('Alice')], bans=[self.s.user('Bob')],
                            wl=[self.s.user('Charlie')], subnets=['10.20.30.0/29'])
        self.s.server_file('A', 'ops.json', [self.s.op('Alice')])
        self.s.server_file('A', 'banned-players.json', [self.s.ban('Bob')])
        self.s.server_file('A', 'whitelist.json', [self.s.user('Charlie')])
        self.s.server_file('A', 'banned-subnets.json', ['10.20.30.0/29'])
        for group in ('ops', 'bans', 'wl', 'subnets'):
            with self.subTest(group=group):
                rules = self.rules(group)
                self.assertTrue(rules)
                self.assertTrue(all(r.rule_scope == 'global' for r in rules))

    def test_global_missing_rules_repaired_on_local_edit(self):
        # On dev this is normal; on acl-fixes it was briefly regressed and restored.
        self.s.write_global(ops=[self.s.user('Alice')], bans=[self.s.user('Alice')],
                            wl=[self.s.user('Alice')], subnets=['10.20.30.0/29'])
        self.s.call('op_user', 'A', 'Bob')
        self.s.call('ban_user', 'A', 'Bob')
        self.s.call('wl_user', 'A', 'Bob')
        self.assertIn('Alice', [x['name'] for x in self.s.read_file('A', 'ops.json')])
        self.assertIn('Alice', [x['name'] for x in self.s.read_file('A', 'banned-players.json')])
        self.assertIn('Alice', [x['name'] for x in self.s.read_file('A', 'whitelist.json')])
        self.assertIn('10.20.30.0/29', self.s.read_file('A', 'banned-subnets.json'))

    def test_global_add_propagates_all_servers(self):
        self.s.add_server('B')
        self.s.ensure_modern_files('B')
        self.s.call('add_global_rule', 'Alice', 'ops')
        self.assertIn('Alice', [r['name'] for r in self.s.read_file('A', 'ops.json')])
        self.assertIn('Alice', [r['name'] for r in self.s.read_file('B', 'ops.json')])

    def test_global_remove_propagates_all_servers(self):
        self.s.add_server('B')
        self.s.ensure_modern_files('B')
        self.s.write_global(ops=[self.s.user('Alice')])
        for srv in ('A', 'B'):
            self.s.server_file(srv, 'ops.json', [self.s.op('Alice')])
        self.s.call('add_global_rule', 'Alice', 'ops', remove=True)
        for srv in ('A', 'B'):
            self.assertNotIn('Alice', [r['name'] for r in self.s.read_file(srv, 'ops.json')])

    def test_global_ip_range_propagation(self):
        self.s.add_server('B')
        self.s.ensure_modern_files('B')
        self.s.call('add_global_rule', '10.20.30.0/29', 'bans')
        for srv in ('A', 'B'):
            self.assertIn('10.20.30.0/29', self.s.read_file(srv, 'banned-subnets.json'))
            self.assertEqual(len(self.s.read_file(srv, 'banned-ips.json')), 6)

    def test_global_ip_whitelist_propagation(self):
        self.s.call('add_global_rule', '10.20.30.0/29', 'bans')
        self.s.call('add_global_rule', '!w10.20.30.3', 'bans')
        self.assertNotIn('10.20.30.3', [v['ip'] for v in self.s.read_file('A', 'banned-ips.json')])

    def test_global_noop_does_not_duplicate_rule(self):
        self.s.write_global(ops=[self.s.user('Alice')])
        self.s.server_file('A', 'ops.json', [self.s.op('Alice')])
        self.s.call('add_global_rule', 'Alice', 'ops')
        self.assertEqual(len(self.s.read_global()['ops']), 1)
        self.assertEqual(len(self.s.read_file('A', 'ops.json')), 1)

    def test_global_rule_uuid_priority_on_rename(self):
        self.require_current('_find_acl_rule')
        self.s.write_global(ops=[self.s.user('OldName')])
        self.s.server_file('A', 'ops.json', [self.s.op('OldName')])
        self.s.call('add_global_rule', 'NewName', 'ops', rename=('OldName', PLAYER_UUIDS['OldName']))
        record = self.s.read_file('A', 'ops.json')
        self.assertEqual(len(record), 1)
        self.assertEqual((record[0]['name'], canonical_uuid(record[0]['uuid'])),
                         ('NewName', PLAYER_UUIDS['OldName']))

    def test_global_ban_rename_preserves_reason_expiry(self):
        self.require_current('_find_acl_rule')
        old = self.s.ban('OldName', reason='Do not drop this reason', expires='2033-01-01 00:00:00 +0000')
        self.s.write_global(bans=[self.s.user('OldName')])
        self.s.server_file('A', 'banned-players.json', [old])
        self.s.call('add_global_rule', 'NewName', 'bans', rename=('OldName', PLAYER_UUIDS['OldName']))
        record = self.s.read_file('A', 'banned-players.json')
        self.assertEqual(len(record), 1)
        self.assertEqual((record[0]['name'], record[0]['reason'], record[0]['expires']),
                         ('NewName', old['reason'], old['expires']))

    def test_global_whitelist_rename_preserves_membership(self):
        self.require_current('_find_acl_rule')
        self.s.write_global(wl=[self.s.user('OldName')])
        self.s.server_file('A', 'whitelist.json', [self.s.user('OldName')])
        self.s.call('add_global_rule', 'NewName', 'wl', rename=('OldName', PLAYER_UUIDS['OldName']))
        data = self.s.read_file('A', 'whitelist.json')
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'NewName')

    def test_global_rename_live_command(self):
        self.require_current('_find_acl_rule')
        running = self.s.running()
        self.s.write_global(ops=[self.s.user('OldName')])
        self.s.server_file('A', 'ops.json', [self.s.op('OldName')])
        self.s.call('add_global_rule', 'NewName', 'ops', rename=('OldName', PLAYER_UUIDS['OldName']))
        self.assertTrue(any('op NewName' in x or x.startswith('deop ') for x in running.commands)
                        or self.s.read_file('A', 'ops.json')[0]['name'] == 'NewName')

    def test_global_ban_does_not_erase_local_bans(self):
        self.s.server_file('A', 'banned-players.json', [self.s.ban('Bob')])
        self.s.call('add_global_rule', 'Alice', 'bans')
        self.assertCountEqual([x['name'] for x in self.s.read_file('A', 'banned-players.json')], ['Alice', 'Bob'])

    def test_global_malformed_config_not_overwritten(self):
        self.require_current('_find_acl_rule')
        self.s.global_path.write_text('NOT VALID JSON', encoding='utf-8')
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            self.s.call('add_global_rule', 'Alice', 'ops')
        self.assertEqual(self.s.global_path.read_text(encoding='utf-8'), 'NOT VALID JSON')

    def test_count_rules_ban_plus_subnets(self):
        m = self.s.manager()
        m.rules['bans'] = [self.s.fn('AclRule')('Alice', 'bans')]
        m.rules['subnets'] = [self.s.fn('AclRule')('10.20.30.0/29', 'subnets')]
        self.assertEqual(m.count_rules('bans')['bans'], 2)

    def test_adjacent_global_rules_cannot_be_removed_locally(self):
        m = self.s.manager()
        self.s.write_global(ops=[self.s.user('Alice'), self.s.user('Bob')])
        m.rules['ops'] = [self.s.fn('AclRule')('Alice', 'ops', is_global=True),
                          self.s.fn('AclRule')('Bob', 'ops', is_global=True),
                          self.s.fn('AclRule')('Charlie', 'ops')]
        self.assertEqual(m._iter_rule_list('ops', 'Alice, Bob, Charlie'), 'Charlie')


    def test_query_parser_single_and_cidr_ip(self):
        m = self.s.manager()
        m._process_query('10.20.30.2, 10.20.31.4/30', 'bans')
        rules = self.s.read_file('A', 'banned-subnets.json')
        self.assertIn('10.20.30.2', rules)
        self.assertIn('10.20.31.4/30', rules)

    def test_query_parser_whitelist_flag(self):
        m = self.s.manager()
        m._process_query('10.20.30.0/29, !w 10.20.30.3', 'bans')
        self.assertIn('!w10.20.30.3', self.s.read_file('A', 'banned-subnets.json'))

    def test_query_parser_global_flag(self):
        m = self.s.manager()
        m._process_query('!g Alice', 'ops')
        self.assertIn('Alice', [x['name'] for x in self.s.read_global()['ops']])

    def test_query_parser_separates_player_and_ip(self):
        m = self.s.manager()
        m._process_query('Alice, 10.20.30.0/29', 'bans')
        self.assertIn('Alice', [x['name'] for x in self.s.read_file('A', 'banned-players.json')])
        self.assertIn('10.20.30.0/29', self.s.read_file('A', 'banned-subnets.json'))

    def test_global_edit_repairs_unrelated_missing_globals(self):
        self.s.write_global(
            ops=[self.s.user('Alice')],
            bans=[self.s.user('Alice')],
            wl=[self.s.user('Alice')],
            subnets=[
                '10.20.30.0/29',
                '!w10.20.30.3',
                '10.20.31.2'
            ]
        )

        # These edits should also repair Alice and the missing IP rules
        self.s.call('add_global_rule', 'Bob', 'ops')
        self.s.call('add_global_rule', 'Bob', 'bans')
        self.s.call('add_global_rule', 'Bob', 'wl')

        self.assertCountEqual(
            [x['name'] for x in self.s.read_file('A', 'ops.json')],
            ['Alice', 'Bob']
        )

        self.assertCountEqual(
            [x['name'] for x in self.s.read_file('A', 'banned-players.json')],
            ['Alice', 'Bob']
        )

        self.assertCountEqual(
            [x['name'] for x in self.s.read_file('A', 'whitelist.json')],
            ['Alice', 'Bob']
        )

        self.assertCountEqual(
            self.s.read_file('A', 'banned-subnets.json'),
            ['10.20.30.0/29', '!w10.20.30.3', '10.20.31.2']
        )

        # The exclusion should cancel the matching generated ban
        ips = [x['ip'] for x in self.s.read_file('A', 'banned-ips.json')]
        self.assertNotIn('10.20.30.3', ips)
        self.assertIn('10.20.31.2', ips)

    def test_global_rename_missing_rule_sends_live_command(self):
        running = self.s.running()
        self.s.write_global(ops=[self.s.user('OldName')])

        self.s.call(
            'add_global_rule', 'NewName', 'ops',
            rename=('OldName', PLAYER_UUIDS['OldName'])
        )

        self.assertIn('op NewName', running.commands)


    def test_global_add_does_not_repeat_playerdb_lookups(self):
        self.s.add_server('B')
        self.s.ensure_modern_files('B')
        self.s.seed_uuid()
        self.s.set_online(True)

        self.s.call('add_global_rule', 'Dave', 'ops')

        self.assertEqual(len(self.s.http_calls), 1)


class TestUUIDDatabase(ACLTestCase):
    def test_cached_lookup_by_name_or_uuid(self):
        a = self.s.call('get_uuid', 'Alice', allow_network=False)
        b = self.s.call('get_uuid', PLAYER_UUIDS['Alice'], allow_network=False)
        self.assertEqual(canonical_uuid(a['uuid']), PLAYER_UUIDS['Alice'])
        self.assertEqual(b['name'], 'Alice')

    def test_offline_lookup_does_not_touch_network(self):
        self.s.set_online(False)
        self.s.call('get_uuid', 'NotInCache')
        self.assertFalse(self.s.http_calls)

    def test_unknown_online_lookup_populates_cache(self):
        self.s.seed_uuid()
        self.s.set_online(True)
        resolved = self.s.call('get_uuid', 'Charlie')
        self.assertEqual(resolved['uuid'], PLAYER_UUIDS['Charlie'])
        self.assertTrue(self.s.http_calls)
        self.s.call('concat_db', reconcile=False)
        self.assertIn('Charlie', [x['name'] for x in self.s.db()])

    def test_stage_multiple_metadata_sources(self):
        self.require_current()
        self.s.call('stage_uuid', {**self.s.user('Alice'), 'latest-ip': '10.1.1.1',
                                    'latest-login': '2026-01-01 10:00:00'}, source='login')
        self.s.call('stage_uuid', {**self.s.user('Alice'), 'ip-geo': 'Somewhere'}, source='playerdb')
        self.s.call('concat_db', reconcile=False)
        r = next(x for x in self.s.db() if x['name'] == 'Alice')
        self.assertEqual(r['latest-ip'], '10.1.1.1')
        self.assertEqual(r['ip-geo'], 'Somewhere')

    def test_newer_login_beats_older_login(self):
        self.require_current()
        self.s.seed_uuid(OldName={'latest-login': '2026-10-01 10:00:00', 'latest-ip': '10.0.0.1'})
        self.s.call('stage_uuid', {**self.s.user('NewName'), 'latest-login': '2026-10-03 10:00:00',
                                    'latest-ip': '10.0.0.3'}, source='login')
        self.s.call('stage_uuid', {**self.s.user('OldName'), 'latest-login': '2026-10-02 10:00:00',
                                    'latest-ip': '10.0.0.2'}, source='login')
        self.s.call('concat_db', reconcile=False)
        item = self.s.db()[0]
        self.assertEqual((item['name'], item['latest-ip'], item['latest-login']),
                         ('NewName', '10.0.0.3', '2026-10-03 10:00:00'))

    def test_usercache_cannot_override_authoritative_login(self):
        self.require_current()
        self.s.seed_uuid(OldName={})
        self.s.call('stage_uuid', {**self.s.user('NewName'), 'latest-login': '2026-10-03 10:00:00'},
                    source='login')
        self.s.call('stage_uuid', self.s.user('OldName'), source='usercache')
        self.s.call('concat_db', reconcile=False)
        self.assertEqual(self.s.db()[0]['name'], 'NewName')

    def test_newer_playerdb_name_when_login_is_old(self):
        self.require_current()
        self.s.seed_uuid(OldName={'latest-login': '2026-09-01 10:00:00'})
        self.s.call('stage_uuid', self.s.user('NewName'), source='playerdb', started_at='2026-10-01 10:00:00')
        self.s.call('concat_db', reconcile=False)
        self.assertEqual(self.s.db()[0]['name'], 'NewName')

    def test_playerdb_cannot_override_login_newer_than_request(self):
        self.require_current()
        self.s.seed_uuid(OldName={'latest-login': '2026-10-05 10:00:00'})
        self.s.call('stage_uuid', self.s.user('NewName'), source='playerdb', started_at='2026-10-03 10:00:00')
        self.s.call('concat_db', reconcile=False)
        self.assertEqual(self.s.db()[0]['name'], 'OldName')

    def test_repeated_idempotent_consolidation(self):
        self.require_current()
        self.s.call('stage_uuid', self.s.user('Alice'), source='usercache')
        self.s.call('concat_db', reconcile=False)
        first = self.s.db()
        self.s.call('concat_db', reconcile=False)
        self.assertEqual(self.s.db(), first)

    def test_concurrent_staging_remains_valid_and_unique(self):
        self.require_current()
        self.s.seed_uuid()
        def run(i):
            name = ['Alice', 'Bob', 'Charlie', 'Dave'][i % 4]
            self.s.call('stage_uuid', {**self.s.user(name), 'ip-geo': 'LAN device'}, source='usercache')
            if i % 7 == 0:
                self.s.call('concat_db', reconcile=False)
        with ThreadPoolExecutor(max_workers=10) as pool:
            list(pool.map(run, range(90)))
        self.s.call('concat_db', reconcile=False)
        records = self.s.db()
        self.assertEqual(len(records), 4)
        self.assertEqual(len({canonical_uuid(x['uuid']) for x in records}), 4)

    def test_corrupted_db_preserves_stage(self):
        self.require_current()
        self.s.uuid_path.write_text('NOT VALID JSON', encoding='utf-8')
        stage_path = self.s.cache / 'uuid-temp' / f"uuid-{PLAYER_UUIDS['Alice']}.json"
        stage_path.parent.mkdir(parents=True, exist_ok=True)
        stage_path.write_text(json.dumps(self.s.user('Alice')), encoding='utf-8')
        self.s.call('concat_db', reconcile=False)
        self.assertEqual(self.s.uuid_path.read_text(encoding='utf-8'), 'NOT VALID JSON')
        self.assertTrue(stage_path.exists())

    def test_newname_display_priority_and_async_refresh(self):
        self.require_current('_find_acl_rule')
        self.s.seed_uuid(OldName={})
        self.s.server_file('A', 'usercache.json', [self.s.user('NewName')])
        m = self.s.manager()
        self.assertIn('NewName', names(m.playerdata))
        self.s.set_online(True)
        m._enrich_cache()
        self.assertTrue(any(PLAYER_UUIDS['OldName'] in url for url in self.s.http_calls))
        self.assertEqual(self.s.db()[0]['name'], 'NewName')

    def test_actual_log_processing_commits_uuid_and_login_time(self):
        m = self.s.manager()
        m._process_log({
            'uuid': PLAYER_UUIDS['OldName'], 'user': 'NewName', 'logged-in': False,
            'ip': '127.0.0.1', 'date': dt(2026, 10, 15, 12, 30, 0),
        })
        self.s.timers[-1].fire()
        item = next(x for x in self.s.db() if canonical_uuid(x['uuid']) == PLAYER_UUIDS['OldName'])
        self.assertEqual(item['name'], 'NewName')
        self.assertEqual(item['latest-login'], '2026-10-15 12:30:00')

    def test_global_reconcile_preserves_uuid(self):
        self.require_current()
        self.s.seed_uuid(OldName={'latest-login': '2026-09-01 10:00:00'})
        self.s.server_file('A', 'ops.json', [self.s.op('OldName')])
        self.s.write_global(ops=[self.s.user('OldName')])
        self.s.call('stage_uuid', self.s.user('NewName'), source='playerdb', started_at='2026-10-01 10:00:00')
        self.s.call('concat_db')
        self.assertEqual(self.s.read_global()['ops'][0]['name'], 'NewName')
        self.assertEqual(self.s.read_file('A', 'ops.json')[0]['uuid'], PLAYER_UUIDS['OldName'])


class TestInitializationAndLegacy(ACLTestCase):
    def test_offline_initialization_has_no_http_calls(self):
        self.s.set_online(False)
        self.s.server_file('A', 'usercache.json', [self.s.user('Alice'), self.s.user('Bob')])
        manager = self.s.manager()
        self.assertTrue(manager.rules is not None)
        self.assertEqual(self.s.http_calls, [])

    def test_existing_usercache_history_loaded(self):
        self.s.server_file('A', 'usercache.json', [self.s.user('Alice'), self.s.user('Bob')])
        manager = self.s.manager()
        self.assert_names(manager.playerdata, ['Alice', 'Bob'])

    def test_whitelist_disabled_does_not_erase_rules(self):
        self.s.server_file('A', 'whitelist.json', [self.s.user('Alice')])
        manager = self.s.manager()
        self.assertIn('Alice', names(manager.rules['wl']))
        self.assertEqual(manager.count_rules()['wl'], 0)

    def test_legacy_read_txt_files_offline(self):
        self.s.servers['A']['version'] = '1.7.5'
        self.s.server_file('A', 'ops.txt', 'alice\nbob\n')
        self.s.server_file('A', 'banned-players.txt', 'charlie\n')
        self.s.server_file('A', 'white-list.txt', 'alice\n')
        self.assertCountEqual([x.lower() for x in names(self.rules('ops'))], ['alice', 'bob'])
        self.assertCountEqual([x.lower() for x in names(self.rules('bans'))], ['charlie'])
        self.assertCountEqual([x.lower() for x in names(self.rules('wl'))], ['alice'])

    def test_legacy_write_stays_txt(self):
        self.s.servers['A']['version'] = '1.7.5'
        self.s.server_file('A', 'ops.txt', 'alice\n')
        self.s.call('op_user', 'A', 'Bob')
        contents = (self.s.servers['A']['path'] / 'ops.txt').read_text(encoding='utf-8').lower()
        self.assertIn('bob', contents)
        self.assertFalse((self.s.servers['A']['path'] / 'ops.json').read_text(encoding='utf-8') != '[]')

    def test_legacy_ip_bans_load(self):
        self.s.servers['A']['version'] = '1.7.5'
        self.s.server_file('A', 'banned-ips.txt', '10.20.30.3\n10.20.30.4\n')
        self.assertCountEqual(names(self.rules('subnets')), ['10.20.30.3', '10.20.30.4'])

    def test_load_acl_post_upgrade_does_not_read_txt(self):
        # Documents a migration gap: automatic conversion is NOT implemented
        # by load_acl(), in either branch. This test is a detector, not a mock
        # of Minecraft's actual first-launch migration.
        self.s.servers['A']['version'] = '1.20.1'
        self.s.server_file('A', 'ops.txt', 'alice\n')
        self.s.server_file('A', 'ops.json', [])
        self.assertNotIn('Alice', names(self.rules('ops')))

    def test_new_server_rule_serialization(self):
        self.s.add_server('N', new=True, whitelist=False)
        manager = self.s.manager('N')
        manager.edit_list('Alice', 'ops')
        manager.edit_list('Bob', 'wl')
        manager.write_rules()
        target = self.s.temp_server
        self.assertTrue((target / 'ops.json').exists())
        self.assertTrue((target / 'whitelist.json').exists())
        self.assertIn('Bob', [x['name'] for x in json.loads((target / 'whitelist.json').read_text(encoding='utf-8'))])

    def test_manager_serialize_excludes_lock(self):
        self.require_current('_find_acl_rule')
        m = self.s.manager()
        serialized = m._to_json()
        self.assertNotIn('_acl_lock', serialized)
        json.dumps(serialized)

    def test_reload_reflects_file_edits(self):
        m = self.s.manager()
        self.s.server_file('A', 'ops.json', [self.s.op('Alice')])
        m.reload_list('ops')
        self.assertIn('Alice', names(m.rules['ops']))
        self.s.server_file('A', 'ops.json', [])
        m.reload_list('ops')
        self.assertEqual(m.rules['ops'], [])

    def test_manager_new_server_global_inheritance(self):
        self.s.write_global(ops=[self.s.user('Alice')], wl=[self.s.user('Bob')])
        self.s.add_server('N', new=True)
        m = self.s.manager('N')
        self.assertIn('Alice', names(m.rules['ops']))
        self.assertIn('Bob', names(m.rules['wl']))

    def test_get_rule_effective_access(self):
        self.s.servers['A']['whitelist'] = True
        self.s.server_file('A', 'ops.json', [self.s.op('Alice')])
        self.s.server_file('A', 'banned-players.json', [self.s.ban('Bob')])
        self.s.server_file('A', 'whitelist.json', [self.s.user('Charlie')])
        m = self.s.manager()
        alice = m.get_rule('Alice')
        self.assertTrue(alice.display_data['op'])
        bob = m.get_rule('Bob')
        self.assertTrue(bob.display_data['ban'])
        charlie = m.get_rule('Charlie')
        self.assertTrue(charlie.display_data['wl'])

    def test_manager_local_edits_then_reload(self):
        m = self.s.manager()
        m.op_player('Alice')
        m.ban_player('Bob')
        m.whitelist_player('Charlie')
        m.reload_list()
        self.assertIn('Alice', names(m.rules['ops']))
        self.assertIn('Bob', names(m.rules['bans']))
        self.assertIn('Charlie', names(m.rules['wl']))

    def test_lockless_global_reload_does_not_need_network(self):
        self.s.set_online(False)
        m = self.s.manager()
        self.s.server_file('A', 'ops.json', [self.s.op('Alice')])
        m.reload_list('ops')
        self.assertFalse(self.s.http_calls)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=pathlib.Path, help='Path to source/core/server/acl.py from either branch')
    args, remaining = parser.parse_known_args()
    if args.source:
        SOURCE = args.source.expanduser().resolve()
    print(f'\nTesting ACTUAL ACL functions from {SOURCE}\n', flush=True)
    unittest.main(argv=[__file__, *remaining], verbosity=2)
