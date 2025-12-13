from datetime import datetime as dt
import subprocess
import requests
import typing
import psutil
import time
import json
import os
import re

if typing.TYPE_CHECKING:
    from source.core.server.manager import ServerObject

from source.core import constants
from source.core.constants import (

    # Directories
    paths,

    # General methods
    folder_check, safe_delete, run_proc, download_url, format_traceback, gen_rstring,

    # Constants
    os_name
)


# Auto-MCS playit integration
# --------------------------------------------- playit.gg Integration --------------------------------------------------

# Handles all methods and data relating to playit.gg integration
class PlayitManager():

    # Raised when a tunnel has an issue being modified
    class TunnelException(BaseException):
        pass

    # Handles tunnel cache for retaining certain tunnel when the API is unreliable
    class TunnelCacheHelper():
        def __init__(self, root_path: str):
            self._path = os.path.join(root_path, 'tunnel-cache.json')
            self._data = {}
            self._read_data()

        def _read_data(self):
            if os.path.exists(self._path):
                with open(self._path, 'r', encoding='utf-8', errors='ignore') as f:
                    self._data = json.loads(f.read())

        def _write_data(self):
            with open(self._path, 'w+') as f:
                f.write(json.dumps(self._data))


        # Delete the cache file and reset
        def clear_cache(self):
            if os.path.exists(self._path): os.remove(self._path)
            self._data = {}

        # Write a tunnel's data to the cache
        def add_tunnel(self, tunnel_id: str, data: dict) -> bool:
            self._data[tunnel_id] = data
            self._write_data()
            return tunnel_id in self._data

        # Remove a tunnel from the cache
        def remove_tunnel(self, tunnel_id: str) -> bool:
            if tunnel_id in self._data:
                del self._data[tunnel_id]
            self._write_data()
            return tunnel_id not in self._data

        # Retrieve the cache from a tunnel
        def get_tunnel(self, tunnel_id: str) -> dict:
            if tunnel_id in self._data:
                return self._data[tunnel_id]
            return {}

    # Houses all tunnel data
    class Tunnel():
        _parent:     'PlayitManager' = None
        _cost:       str  = None

        id:          str  = None
        status:      str  = None
        in_use:      bool = None
        region:      str  = None
        type:        str  = None
        protocol:    str  = None
        port:        int  = None
        host:        str  = None
        domain:      str  = None
        remote_port: int  = None
        hostname:    str  = None
        created:     dt   = None

        def __init__(self, _parent: 'PlayitManager', tunnel_data: dict):
            self._parent = _parent
            self._cost = tunnel_data['port_count']
            self.id = tunnel_data['id']
            self.type = tunnel_data['tunnel_type'] if tunnel_data['tunnel_type'] else 'both'
            self.protocol = tunnel_data['port_type']

            # if Tunnel is not ready
            self.status = tunnel_data['alloc']['status']
            if self.status == 'pending': return

            # Format networking data
            self.region = tunnel_data['alloc']['data']['region']

            # Mechanism to load data from cache if it's missing from the API
            try:
                self.port = int(tunnel_data['origin']['data']['local_port'])
                self.host = tunnel_data['origin']['data']['local_ip']
            except:

                # If tunnel is not cached and port is unknown, delete itself
                try:
                    cached_data = self._parent.tunnel_cache.get_tunnel(self.id)
                    self.port = int(cached_data['local_port'])
                    self.host = cached_data['local_ip']
                except:
                    self.delete()

            # Format playit tunnel data
            self.domain = tunnel_data['alloc']['data']['assigned_domain']
            self.remote_port = int(tunnel_data['alloc']['data']['port_start'])
            self.hostname = f'{self.domain}:{self.remote_port}' if self.type == 'both' else self.domain


            date_object = dt.fromisoformat(tunnel_data['created_at'].replace("Z", "+00:00"))
            timezone = dt.now().astimezone().tzinfo
            self.created = date_object.astimezone(timezone)

            # If this tunnel is currently assigned to a ServerObject
            self.in_use = False

        def __repr__(self):
            return f"<PlayitManager.{self.__class__.__name__} '{self.hostname}'>"

        def delete(self):
            self._parent._delete_tunnel(self)

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        from source.core import logger
        return logger.send_log(f'{__name__}.{self.__class__.__name__}', message, level, 'playit')

    def __init__(self):
        self._git_base = "https://github.com/playit-cloud/playit-agent/releases"
        self._api_base = "https://api.playit.gg"
        self._web_base = "https://playit.gg"

        self._exec_version = {
            'windows': '0.16.2',
            'linux':   '0.16.2',
            'macos':   '0.15.13'
        }[os_name]

        self._download_url = {
            'windows': f'{self._git_base}/download/v{self._exec_version}/playit-windows-x86_64-signed.exe',
            'linux':   f'{self._git_base}/download/v{self._exec_version}/playit-linux-{"aarch" if constants.is_arm else "amd"}64',
            'macos':   f'{self._git_base}/download/v{self._exec_version}/playit-darwin-{"arm" if constants.is_arm else "intel"}'
        }[os_name]

        self._filename = {
            'windows': 'playit.exe',
            'linux':   'playit',
            'macos':   'playit'
        }[os_name]


        # General stuff
        self.provider = 'playit'
        self.directory = paths.playit
        self.exec_path = os.path.join(self.directory, self._filename)
        self.toml_path = os.path.join(self.directory, 'playit.toml')
        self.tunnel_cache = self.TunnelCacheHelper(self.directory)
        self.config = {}

        self.initialized = False
        self.session = requests.Session()
        self.service = None


        # Client info
        self.agent_web_url = None
        self.max_tunnels = 4
        self.tunnels = {'tcp': [], 'udp': [], 'both': []}

        self._agent_id    = None   # Installed agent ID (executable)
        self._proto_key   = None   # Protocol registry key
        self._session_key = None   # For login URL to guest account
        self._secret_key  = None   # For authentication to guest account



    # ----- OS/filesystem handling -----
    # Check if the agent is installed
    def _check_agent(self) -> bool:
        return os.path.isfile(self.exec_path)

    # Load playit.toml into an attribute
    def _load_config(self) -> bool:
        if os.path.exists(self.toml_path):
            with open(self.toml_path, 'r', encoding='utf-8', errors='ignore') as toml:
                self._send_log(f"loading playit configuration from '{self.toml_path}'")
                strip_list = "'\" \n"
                self.config = {
                    k.strip(strip_list): v.strip(strip_list)
                    for k, v in (line.split('=', 1) for line in toml.readlines())
                }
        return bool(self.config)

    # Deletes config and starts over
    def _reset_config(self) -> bool:
        if os.path.exists(self.toml_path):
            os.remove(self.toml_path)

        reset = not os.path.exists(self.toml_path)

        if reset:
            self.config = {}
            self._send_log('successfully reset playit configuration')
        else: self._send_log('failed to reset playit configuration', 'error')

        return reset

    # Download and install the agent
    def install_agent(self, progress_func: callable = None) -> bool:

        if not constants.app_online:
            log_content = "Downloading playit requires an internet connection"
            self._send_log(log_content, 'error')
            raise ConnectionError(log_content)

        if self.service:
            log_content = "Can't re-install while playit is running"
            self._send_log(log_content, 'error')
            raise RuntimeError(log_content)


        # If ngrok is present, delete it
        ngrok = os.path.join(paths.tools, ('ngrok-v3.exe' if os_name == 'windows' else 'ngrok-v3'))
        if os.path.exists(ngrok):
            os.remove(ngrok)

        # Delete current version first
        final_path = os.path.join(self.directory, self._filename)
        self._send_log(f"installing playit agent from '{self._download_url}' to '{final_path}'...", 'info')
        if self._check_agent():
            os.remove(self.exec_path)

        # Install the new version
        folder_check(self.directory)
        download_url(self._download_url, self._filename, self.directory, progress_func)

        # chmod if UNIX-based
        if os_name != 'windows':
            run_proc(f'chmod +x "{self.exec_path}"')


        success = self._check_agent()
        if success: self._send_log(f"successfully installed playit agent to '{final_path}'", 'info')
        else:       self._send_log(f"something went wrong installing playit agent from '{self._download_url}'", 'error')

        return success

    # Removes the agent from the filesystem
    def uninstall_agent(self, keep_config=True) -> bool:

        if not self._check_agent():
            self._send_log("can't uninstall as playit isn't installed")
            return True

        if self.service:
            log_content = "Can't delete while playit is running"
            self._send_log(log_content, 'error')
            raise RuntimeError(log_content)

        if os.path.exists(self.directory):
            self._send_log(f"deleting playit agent and configuration from '{self.directory}'", 'info')
            os.remove(self.exec_path) if keep_config else safe_delete(self.directory)

        return not self._check_agent()

    # Updates the agent to the latest version
    def update_agent(self) -> bool:
        success = False

        if self._check_agent():
            try:
                uninstalled = self.uninstall_agent()
                self.tunnel_cache.clear_cache()
                installed   = self.install_agent()
                success = uninstalled and installed

            except Exception as e:
                self._send_log(f'failed to update the playit client: {format_traceback(e)}', 'error')

            if success: self._send_log('successfully updated the playit client ', 'info')

        return success

    # Starts the agent and returns status
    def _start_agent(self) -> bool:

        if not self.service:
            self.service = subprocess.Popen(f'"{self.exec_path}" -s --secret_path "{self.toml_path}"', stdout=subprocess.PIPE, shell=True)
            self._send_log(f"launched playit agent with PID {self.service.pid}")

        return self.service is not None and self.service.poll() is None

    # Stops the agent and returns output
    def _stop_agent(self) -> str:

        # Kill service if it's currently running
        if self.service and self.service.poll() is None:
            pid = self.service.pid

            # Iterate over self and children to find playit process
            try:             parent = psutil.Process(self.service.pid)
            except KeyError: parent = self.service

            # Windows
            if os_name == "windows":
                children = parent.children(recursive=True)
                for proc in children:
                    if proc.name() == "playit.exe":
                        run_proc(f"taskkill /f /pid {proc.pid}")
                        break

            # macOS
            elif os_name == "macos":
                if parent.name() == "playit":
                    run_proc(f"kill {parent.pid}")

            # Linux
            else:
                if parent.name() == "playit":
                    run_proc(f"kill {parent.pid}")
                else:
                    children = parent.children(recursive=True)
                    for proc in children:
                        if proc.name() == "playit":
                            run_proc(f"kill {proc.pid}")
                            break

            self.service.kill()
            self._send_log(f"stopped playit agent with PID {pid}")

        return_code = self.service.poll() if self.service else 0
        del self.service
        self.service = None

        return return_code



    # ----- API auth handling -----
    # Retrieves claim code from the console output
    def _get_claim_code(self) -> str | None:
        if self.service:

            # Loop over output for claim code
            url = f'{self._web_base}/claim/'
            code = None

            # Be careful with this, it could potentially wait for a new line forever
            for line in iter(self.service.stdout.readline, ""):
                if url in line.decode():
                    code = line.decode().split(url)[-1].strip()
                    break

            return code

    # Claim the agent as a guest user
    def _claim_agent(self) -> bool:
        self._start_agent()

        try:
            # Retrieve and sanitize code from the client
            claim_code = self._get_claim_code()
            if not claim_code:
                raise RuntimeError("Could not read claim code from agent output")

            m = re.search(r'[A-Za-z0-9]{10}', str(claim_code))
            if not m:
                raise RuntimeError(f"Malformed claim code from agent: {claim_code!r}")
            claim_code = m.group(0).lower()

            agent_type = "self-managed"
            version    = self._exec_version


            # Create guest session, and use bearer auth for claim/* calls
            guest = self.session.post(f"{self._api_base}/login/create/guest", json={}).json()
            if guest.get("status") != "success":
                raise RuntimeError(f"login/create/guest failed: {guest}")

            self._session_key = guest["data"]["session_key"]
            self.session.headers["Authorization"] = f"bearer {self._session_key}"
            self.session.headers["Content-Type"] = "application/json"


            # Wait for agent to register the code (up to 60s)
            for _ in range(60):

                details = self._request("claim/details", json={
                    "code": claim_code,
                    "agent_type": agent_type,
                    "version": version
                })

                if details.get("status") == "success":
                    break

                reason = details.get("data")
                if reason == "WaitingForAgent":
                    time.sleep(1)
                    continue

                if reason in ("CodeNotFound", "ClaimExpired"):
                    raise RuntimeError(f"claim/details: {reason} (code is likely invalid, or stale)")

                raise RuntimeError(f"claim/details failed: {details}")
            else: raise RuntimeError("claim/details never became ready (agent didn't register in time)")


            # Claim setup prior to accept
            setup = self._request("claim/setup", json={
                "code": claim_code,
                "agent_type": agent_type,
                "version": version
            })

            if setup.get("status") != "success":
                raise RuntimeError(f"claim/setup failed: {setup}")


            # Accept the claim
            accept = self._request("claim/accept", json={
                "code": claim_code,
                "name": f"from-key-{claim_code[:4]}",
                "agent_type": agent_type
            })
            if accept.get("status") != "success":
                raise RuntimeError(f"claim/accept failed: {accept}")


            # Exchange the claim for the account's secret key
            exchange = None
            for _ in range(30):

                exchange = self._request("claim/exchange", json={"code": claim_code})
                if exchange.get("status") == "success":
                    self._secret_key = exchange["data"]["secret_key"]
                    break

                if exchange.get("data") == "NotAccepted":
                    time.sleep(1)
                    continue

                if exchange.get("data") in ("CodeNotFound", "ClaimExpired"):
                    raise RuntimeError(f"claim/exchange failed: {exchange}")

                raise RuntimeError(f"claim/exchange failed: {exchange}")

            else: raise RuntimeError(f"claim/exchange still not ready: {exchange}")

            self._send_log("successfully claimed playit agent to account")


        finally: self._stop_agent()
        return bool(self._secret_key)

    # Register client protocol version with the server
    def _proto_register(self) -> bool:
        proto_data = {
            'agent_version': {
                'official': True,
                'details_website': None,
                'version': {
                    'platform': os_name,
                    'version': self._exec_version
                }
            },
            'client_addr': '0.0.0.0:0',
            'tunnel_addr': '0.0.0.0:0'
        }

        response = self._request('proto/register', json=proto_data)
        if 'status' in response and response['status'] == 'success':
            self._proto_key = response['data']['key']

        return bool(self._proto_key)


    # ----- API tunnel handling -----
    def _request(self, endpoint: str, *args, **kwargs):
        return self.session.post(f"{self._api_base}/{endpoint.strip('/')}", *args, **kwargs).json()

    # Creates two lists of all tunnels, sorted by protocol
    def _retrieve_tunnels(self) -> dict:
        self.tunnels = {'tcp': [], 'udp': [], 'both': []}

        data = self._request('tunnels/list', json={"agent_id": self._agent_id})
        if data['status'] == 'success':

            # Update maximum tunnels allowed by account (seems to be inaccurate)
            # self.max_tunnels = data['data']['tcp_alloc']['allowed']

            # Create tunnel objects from tunnels
            for tunnel_data in data['data']['tunnels']:
                tunnel = self.Tunnel(self, tunnel_data)
                self.tunnels[tunnel.protocol].append(tunnel)

        return self.tunnels

    # Returns consolidated list of every tunnel
    def _return_single_list(self) -> list:
        single_list = self.tunnels['tcp']
        single_list.extend(self.tunnels['udp'])
        single_list.extend(self.tunnels['both'])
        return single_list

    # Returns True if any tunnels are in use
    def _tunnels_in_use(self) -> bool:
        return any([t.in_use for t in self._return_single_list()])

    # Returns False if protocol type exceeds the max tunnel limit
    # protocol: 'tcp', 'udp', or 'both'
    def _check_tunnel_limit(self) -> bool:
        tunnel_count = sum(t._cost for t in self.tunnels['both'])
        tunnel_count += sum(t._cost for t in self.tunnels['tcp'])
        tunnel_count += sum(t._cost for t in self.tunnels['udp'])
        return not bool(tunnel_count >= self.max_tunnels)

    # Create a tunnel with
    # protocol: 'tcp', 'udp', or 'both'
    def _create_tunnel(self, port: int = 25565, protocol: str = 'tcp') -> Tunnel | None:
        if port not in range(1024, 65535):
            port = 25565

        # Can't exceed maximum tunnels specified
        if not self._check_tunnel_limit():
            raise self.TunnelException(f"This account can't create more than {self.max_tunnels} tunnel(s)")

        tunnel_type = {
            'tcp': 'minecraft-java',
            'udp': 'minecraft-bedrock',
            'both': None
        }[protocol]

        tunnel_data = {
            "name": f'{tunnel_type}_{gen_rstring(4).lower()}',
            "tunnel_type": tunnel_type,
            "port_type": protocol,
            "port_count": 2 if protocol == 'both' else 1,
            "enabled": True,
            "origin": {
                "type": "agent",
                "data": {
                    "agent_id": self._agent_id,
                    "local_ip": '127.0.0.1',
                    "local_port": port,
                },
            },
        }


        # Send the request to create a tunnel
        try:
            data = self._request('tunnels/create', json=tunnel_data)
            tunnel_id = data['data']['id']

            # Success
            if tunnel_id:
                self.tunnel_cache.add_tunnel(tunnel_id, tunnel_data)

                # Wait until tunnel is live (up to 15s)
                for _ in range(15):
                    self._retrieve_tunnels()

                    # Lookup method to reverse search the actual ID
                    for tunnel in self.tunnels[protocol]:
                        if tunnel.status != 'pending' and tunnel_id == tunnel.id:
                            self._send_log(f"successfully created a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")
                            return tunnel

                    time.sleep(1)

        except Exception as e:
            self._send_log(f"failed to create a tunnel for '{protocol}:{port}': {format_traceback(e)}")

    # Delete a tunnel with the object
    def _delete_tunnel(self, tunnel: Tunnel) -> bool:
        tunnel_status = self._request('tunnels/delete', json={'tunnel_id': tunnel.id})

        if tunnel_status['status'] == 'success':
            self.tunnel_cache.remove_tunnel(tunnel.id)
            self.tunnels[tunnel.protocol].remove(tunnel)
            self._send_log(f"successfully deleted a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")
            return tunnel not in self.tunnels[tunnel.protocol]

        return False

    # Deletes all tunnels
    def _clear_tunnels(self) -> dict:
        [tunnel.delete() for tunnel in self.tunnels['tcp']]
        [tunnel.delete() for tunnel in self.tunnels['udp']]
        [tunnel.delete() for tunnel in self.tunnels['both']]
        self.tunnels = {'tcp': [], 'udp': [], 'both': []}
        return self.tunnels



    # ----- General use -----
    # Configures the playit session and retrieves the agent key
    def initialize(self, _attempt: int = 0) -> bool:
        if not self._check_agent():
            return False

        # If a .toml isn't generated, the guest is unclaimed
        if not os.path.exists(self.toml_path):
            self._claim_agent()
            if not os.path.exists(self.toml_path):
                with open(self.toml_path, 'w+') as f:
                    f.write(f'secret_key = "{self._secret_key}"\n')

        # Otherwise, get the secret key from .toml
        else:
            try:
                self._load_config()
                self._secret_key = self.config['secret_key']

            # If the key couldn't be retrieved, delete .toml and try again
            except KeyError:
                self._reset_config()
                if _attempt >= 3: raise RuntimeError('Unable to initialize playit agent')
                return self.initialize(_attempt + 1)

        # Agent ID
        self.session.headers['Authorization'] = f'agent-key {self._secret_key}'
        agent_data = self._request('agents/rundata')
        self._agent_id = agent_data['data']['agent_id']

        # Get login URL
        guest_data = self._request('login/guest')
        self._session_key = guest_data['data']['session_key']
        self.agent_web_url = f'{self._web_base}/login/guest-account/{self._session_key}'

        # Register client protocol
        self._proto_register()

        # Get current tunnels
        self._retrieve_tunnels()

        self.initialized = True
        self._send_log(f"initialized playit agent, login from this url (select 'continue as guest'):\n{self.agent_web_url}", 'info')
        return self.initialized

    # Get a tunnel by port and (optionally type)
    # Will recycle old tunnels if a new one needs to be made to not exceed the account limit
    # protocol: 'tcp', 'udp', or 'both'
    def get_tunnel(self, port: int, protocol: str = 'tcp', ensure: bool = False) -> Tunnel | None:
        self._retrieve_tunnels()

        for tunnel in self.tunnels[protocol]:
            if tunnel.port == int(port) and not tunnel.in_use:
                return tunnel

        # If ensure is True, create the tunnel if it doesn't exist
        else:
            if ensure:

                # Remove the oldest tunnel before creating a new once if limit is exceeded
                if not self._check_tunnel_limit():
                    for tunnel in sorted(self._return_single_list(), key=lambda t: t.created):
                        tunnel.delete()
                        if self._check_tunnel_limit():
                            break

                return self._create_tunnel(port, protocol)

    # Initializes tunnel for a server object
    def start_tunnel(self, server_obj: 'ServerObject') -> Tunnel | None:
        if not self.initialized:
            if not self.initialize(): return None

        port = int(server_obj.run_data['network']['address']['port'])
        protocol = 'both' if server_obj.geyser_enabled else 'tcp'

        tunnel = self.get_tunnel(port, protocol, ensure=True)
        if tunnel:
            tunnel.in_use = True

            # Add the tunnel to the server's run_data
            server_obj.run_data['playit-tunnel'] = tunnel

            # Ignore the tunnel with server_obj._telepath_run_data()
            self._start_agent()
            self._send_log(f"started a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")

        return tunnel

    # Stops the current tunnel of the server object
    def stop_tunnel(self, server_obj: object) -> False:
        if not self.initialized:
            return False

        # Get tunnel from run_data
        tunnel = server_obj.run_data['playit-tunnel']
        tunnel.in_use = False

        # Stop agent only if no tunnels are in use
        if not self._tunnels_in_use() and self.service:
            self._send_log(f"stopped a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")
            self._stop_agent()

# Global playit.gg manager
manager: PlayitManager | None = None

def init_manager():
    global manager
    if not manager: manager = PlayitManager()
