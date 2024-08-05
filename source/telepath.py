from fastapi import FastAPI, Body, File, UploadFile, HTTPException, Request, Depends, status
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from fastapi.responses import JSONResponse, FileResponse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import Callable, get_type_hints, Optional
from cryptography.hazmat.primitives import hashes
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, create_model
from cryptography.fernet import Fernet
from datetime import timedelta as td
from datetime import datetime as dt
from datetime import timezone as tz
from jwt import InvalidTokenError
from operator import itemgetter
from munch import Munch
from glob import glob
import machineid
import threading
import requests
import inspect
import uvicorn
import logging
import hashlib
import codecs
import random
import bcrypt
import string
import base64
import json
import time
import jwt
import os

# Local imports
from amscript import AmsFileObject, ScriptManager
from addons import AddonFileObject, AddonManager
from acl import AclManager, AclRule
from backup import BackupManager
from svrmgr import ServerObject
import constants
import svrmgr


# Auto-MCS Telepath API
# This library abstracts auto-mcs functionality to control servers remotely
# ----------------------------------------------- Global Variables -----------------------------------------------------

# Create ID_HASH to use for authentication so the token can be reset
telepath_settings = constants.app_config.telepath_settings
if 'id_hash' not in telepath_settings or not telepath_settings['id_hash']:
    ID_HASH = codecs.encode(os.urandom(32), 'hex').decode()
    telepath_settings['id_hash'] = ID_HASH
else:
    ID_HASH = telepath_settings['id_hash']

SECRET_KEY = os.urandom(64)
UNIQUE_ID = machineid.hashed_id(f'{constants.app_title}::{constants.username}::{ID_HASH}')
ALGORITHM = "HS256"
AUTH_KEYPAIR_EXPIRE_SECONDS = 5
ACCESS_TOKEN_EXPIRE_MINUTES = 30
PAIR_CODE_EXPIRE_MINUTES = 1.5


# Instantiate the API if main
def create_schema():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="auto-mcs - Telepath API",
        version=TelepathManager.version,
        summary="Welcome to the auto-mcs Telepath API! You can use this utility for seamless remote management.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": TelepathManager.doc_logo}
    app.openapi_schema = openapi_schema
    return app.openapi_schema
def get_docs_url(type: str):
    if not constants.app_compiled:
        return "/docs" if "docs" in type else "/redoc"
app = FastAPI(docs_url=get_docs_url("docs"), redoc_url=get_docs_url("redoc"))
app.openapi = create_schema


# Internal wrapper for API functionality
class TelepathManager():
    version = constants.telepath_version
    doc_logo = "https://github.com/macarooni-man/auto-mcs/blob/main/source/gui-assets/logo.png?raw=true"
    default_host = "0.0.0.0"
    default_port = 7001

    def __init__(self):
        global app
        self.app = app
        self.config = None
        self.server = None
        self.running = False
        self.host = self.default_host
        self.port = self.default_port
        self.sessions = {}
        self.jwt_tokens = {}
        self.update_config(host=self.host, port=self.port)

        # Helper classes for security
        self.auth = AuthHandler()
        self.secret_file = SecretHandler()
        self.logger = AuditLogger()

        # Server side data
        self.current_user = None
        self.pair_data = {}
        self.pair_listen = True

        # Load authenticated users from saved data
        self.authenticated_sessions = []
        self._read_session()
        # [{'host1': str, 'user': str, 'id': str}, {'host2': str, 'user': str, 'id': str}]
        # .....

        # Disable low importance uvicorn logging
        if not constants.debug:
            logging.getLogger("uvicorn.error").handlers = []
            logging.getLogger("uvicorn.error").propagate = False
            logging.getLogger("uvicorn.access").handlers = []
            logging.getLogger("uvicorn.access").propagate = False

    def _run_uvicorn(self):
        self.server = uvicorn.Server(self.config)
        self.server.run()

    def _kill_uvicorn(self):
        self.server.should_exit = True

    def _encrypt_id(self, id: str):
        pwd_bytes = id.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
        hashed_password = hashed_password.decode("utf-8")
        return hashed_password

    def _verify_id(self, raw_id: str, hashed_id: str):
        password_byte_enc = raw_id.encode("utf-8")
        hashed_password_enc = hashed_id.encode("utf-8")
        return bcrypt.checkpw(
            password=password_byte_enc, hashed_password=hashed_password_enc
        )

    def _return_token(self, session: dict):
        session = constants.deepcopy(session)
        del session['id']
        return {
            'access-token': create_access_token(session),
            'hostname': constants.hostname,
            'os': constants.os_name,
            'app-version': constants.app_version,
            'telepath-version': self.version
        }

    def _save_session(self, session: dict):
        self.authenticated_sessions.append(session)
        self.secret_file.write(self.authenticated_sessions)

        # Eventually add code here to save and reload this from a file

    def _read_session(self):
        self.authenticated_sessions = self.secret_file.read()

    def _create_pair_code(self, host: dict, id: str):
        characters = string.ascii_letters + string.digits
        code = str(''.join(random.choice(characters) for _ in range(6)).upper()).replace('O', '0')

        # {'host': IP address, 'username': pass in constants.username}
        self.pair_data = {
            "host": host,
            "id": self._encrypt_id(id),
            "code": code,
            "attempt": 0,
            "expire": (dt.now() + td(minutes=PAIR_CODE_EXPIRE_MINUTES)),
        }

        # Expire code automatically
        def _clear_pair_code(*a):
            try:
                if self.pair_data['code'] == code:
                    self.pair_data = {}
            except:
                pass

        threading.Timer((PAIR_CODE_EXPIRE_MINUTES * 60), _clear_pair_code).start()

    def _update_user(self, session=None):
        self.current_user = session
        self.logger.current_user = self.current_user

    def update_config(self, host: str, port: int):
        self.host = host
        self.port = port
        self.config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            # workers=1,
            # limit_concurrency=1,
            # limit_max_requests=1
        )

        # Restart if running
        if self.running:
            self.restart()

    def start(self):
        if not self.running:
            self.running = True
            threading.Timer(0, self._run_uvicorn).start()

            message = f'initialized API on "{self.host}:{self.port}"'
            if not constants.headless:
                print(f'[INFO] [telepath] {message}')
            else:
                return message
        elif constants.headless:
            return 'Telepath API is already running'

    def stop(self):
        # This still doesn't work for whatever reason?
        if self.running:
            self._kill_uvicorn()
            self.server = None
            self.running = False

            message = f'disabled API on "{self.host}:{self.port}"'
            if not constants.headless:
                print(f'[INFO] [telepath] {message}')
            else:
                return message
        elif constants.headless:
            return 'Telepath API is not running'

    def restart(self):
        self.stop()
        time.sleep(1)
        self.start()

    # Send a POST or GET request to an endpoint
    def _get_headers(self, host: str, only_token=False):
        headers = {}
        if not only_token:
            headers = {"Content-Type": "application/json"}
        if host in self.jwt_tokens:
            headers['Authorization'] = f'Bearer {self.jwt_tokens[host]}'
        return headers
    def _get_session(self, host: str, port: int):
        if host in self.sessions:
            session = self.sessions[host]['session']
        else:
            session = requests.Session()
            self.sessions[host] = {'port': port, 'session': session}
            print(f"[INFO] [telepath] Opening session to '{host}'")
        return session
    def request(self, endpoint: str, host=None, port=None, args=None, timeout=120):
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        if endpoint.endswith('/'):
            endpoint = endpoint[:-1]
        if not host:
            host = self.host
        if not port:
            port = self.port

        # Retrieve token for auth and set headers
        url = f"http://{host}:{port}/{endpoint}"
        headers = self._get_headers(host)

        # Check if session exists
        session = self._get_session(host, port)

        # Determine POST or GET based on params
        data = session.post(url, headers=headers, json=args, timeout=timeout) if args is not None else session.get(url, headers=headers, timeout=timeout)

        if not data:
            return None

        json_data = data.json()
        if isinstance(json_data, dict) and "__reconstruct__" in json_data:
            return reconstruct_object(json_data)

        return json_data

    def close_sessions(self):
        for host, data in self.sessions.items():

            # Log out if authenticated to host
            if host in self.jwt_tokens:
                self.logout(host, data['port'])

            # Close the requests session
            data['session'].close()
            print(f"[INFO] [telepath] Closed session to '{host}:{data['port']}'")


    # -------- Internal endpoints to authenticate with telepath -------- #

    # Returns data for pairing a remote session
    # host = {'host': str, 'user': str}
    def _request_pair(self, host: dict, id_hash: bytes, request: Request) -> dict or None:
        if not self.pair_listen:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ignoring pair requests")

        error_code = status.HTTP_418_IM_A_TEAPOT if random.randrange(10) == 1 else status.HTTP_409_CONFLICT
        if constants.ignore_close:
            message = "Server is busy, please try again later"
            print(f'[INFO] [telepath] {message}')
            raise HTTPException(status_code=error_code, detail=message)

        # Ignore request if there's currently a valid pairing code
        if self.pair_data:
            message = "Please wait for the current code to expire"
            print(f'[INFO] [telepath] {message}')
            raise HTTPException(status_code=error_code, detail=message)

        # Ignore an improperly formatted request
        try:
            host['ip'] = request.client.host
            test = host['host']
            test = host['user']
        except:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid request')

        # If there is no pair code, and the service is running
        if self.running:
            ip = request.client.host
            id = self.auth._decrypt(id_hash, ip)
            self._create_pair_code(host, id)

            # Show pop-up if the UI is open
            if constants.telepath_pair:
                constants.telepath_pair.open(self.pair_data)

            print(f"[INFO] [telepath] Generated pairing code: {self.pair_data['code']} for host: {host}")
            return True
        else:
            print(f'[INFO] [telepath] Telepath API is not running')
            return False

    def _submit_pair(self, host: dict, id_hash: bytes, code: str, request: Request):
        if self.running:
            ip = request.client.host
            id = self.auth._decrypt(id_hash, ip)

            if not self.pair_listen:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ignoring pair requests")

            if not self.pair_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A pair code hasn't been generated")

            if dt.now() < self.pair_data['expire']:

                # First, make sure that the user, id, and code match
                if host['host'] == self.pair_data['host']['host'] and host['user'] == self.pair_data['host']['user'] and ip == self.pair_data['host']['ip']:
                    if self._verify_id(id, self.pair_data['id']) and code == self.pair_data['code']:
                        # Successfully authenticated

                        # Call function to write this data to a file
                        session = {'host': host['host'], 'user': host['user'], 'id': self.pair_data['id'], 'ip': ip}
                        self.pair_data = {}
                        self._save_session(session)
                        self._update_user(session)
                        return self._return_token(session)

                # Expire after 3 failed attempts
                self.pair_data['attempt'] += 1
                if self.pair_data['attempt'] >= 3:
                    self.pair_data = {}
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid host or pair code')

            else:
                self.pair_data = {}
                return False

    def _login(self, host: dict, id_hash: bytes, request: Request):
        if self.running:
            ip = request.client.host
            id = self.auth._decrypt(id_hash, ip)

            for session in self.authenticated_sessions:
                if self._verify_id(id, session['id']):

                    # This can change later, but currently, there can only be one telepath user globally
                    if self.current_user and not (self.current_user['id'] == session['id'] and self.current_user['ip'] == request.client.host):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Logged in from another session",
                            headers={"WWW-Authenticate": "Bearer"},
                        )

                    session['host'] = host['host']
                    session['user'] = host['user']
                    session['ip'] = request.client.host
                    self._update_user(session)
                    return self._return_token(session)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _logout(self, host: dict, request: Request):
        ip = request.client.host
        if self.current_user:
            if ip == self.current_user['ip'] and host['host'] == self.current_user['host'] and host['user'] == self.current_user['user']:
                self.current_user = {}
                return True

        return False


    # --------- Client-side functions to call the endpoints from a remote device -------- #
    def login(self, ip: str, port: int):

        # Get the server's public key and create an encrypted token
        token = self.auth.public_encrypt(ip, port, UNIQUE_ID)
        url = f"http://{ip}:{port}/telepath/login"
        host_data = {
            'host': {'host': constants.hostname, 'user': constants.username},
            'id_hash': token
        }

        # Eventually add a retry algorithm

        try:
            session = self._get_session(ip, port)
            data = session.post(url, json=host_data).json()
            if 'access-token' in data:
                self.jwt_tokens[ip] = data['access-token']
                return_data = constants.deepcopy(data)
                del return_data['access-token']
                return_data['host'] = ip
                return_data['port'] = port
                return_data['added-servers'] = {}
                return_data['nickname'] = ''
                return return_data
            else:
                return {}
        except:
            pass
        return {}

    def logout(self, ip: str, port: int):
        url = f"http://{ip}:{port}/telepath/logout"
        host_data = {'host': constants.hostname, 'user': constants.username}

        # Eventually add a retry algorithm
        try:
            session = self._get_session(ip, port)
            data = session.post(url, json=host_data, headers=self._get_headers(ip)).json()
            print(f"[INFO] [telepath] Logged out from '{ip}:{port}'")
            return data
        except:
            pass
        return False

    def request_pair(self, ip: str, port: int):

        # Get the server's public key and create an encrypted token
        token = self.auth.public_encrypt(ip, port, UNIQUE_ID)
        url = f"http://{ip}:{port}/telepath/request_pair"
        host_data = {
            'host': {'host': constants.hostname, 'user': constants.username},
            'id_hash': token
        }

        # Eventually add a retry algorithm

        try:
            data = requests.post(url, json=host_data).json()
            return data
        except:
            pass
        return None

    def submit_pair(self, ip: str, port: int, code: str):

        # Get the server's public key and create an encrypted token
        token = self.auth.public_encrypt(ip, port, UNIQUE_ID)
        url = f"http://{ip}:{port}/telepath/submit_pair?code={code}"
        host_data = {
            'host': {'host': constants.hostname, 'user': constants.username},
            'id_hash': token
        }

        # Eventually add a retry algorithm

        try:
            data = requests.post(url, json=host_data).json()
            if 'access-token' in data:
                self.jwt_tokens[ip] = data['access-token']
                return_data = constants.deepcopy(data)
                del return_data['access-token']
                return_data['host'] = ip
                return_data['port'] = port
                return_data['added-servers'] = {}
                return_data['nickname'] = ''
                return return_data
        except:
            pass
        return None



# ------------------------------------------ Authentication & Encryption -----------------------------------------------

# Houses PKI for authentication
class AuthHandler():
    def __init__(self):
        self.key_pairs = {}
        self.sha256 = hashes.SHA256()

    # Server side functionality
    def _create_key_pair(self, ip: str):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.key_pairs[ip] = private_key

        # Expire this keypair after a delay
        def expire_keypair(*a):
            if ip in self.key_pairs:
                if private_key == self.key_pairs[ip]:
                    del self.key_pairs[ip]
        threading.Timer(AUTH_KEYPAIR_EXPIRE_SECONDS, expire_keypair).start()

        return private_key.public_key()

    def _get_public_key(self, ip: str, expire_immediately=True):
        public_key = None
        if ip not in self.key_pairs:
            public_key = self._create_key_pair(ip)

        elif not expire_immediately:
            public_key = self.key_pairs[ip].public_key()


        # Convert public key to PEM for web serialization
        if public_key:
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem

        # Throw error if key has expired
        raise HTTPException(status_code=status.HTTP_425_TOO_EARLY, detail="Can't retrieve the public key at this time")

    def _decrypt(self, token: str, ip: str) -> str or False:
        cipher_text = base64.b64decode(token)

        if ip in self.key_pairs:
            decrypted_content = self.key_pairs[ip].decrypt(
                cipher_text,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=self.sha256),
                    algorithm=self.sha256,
                    label=None
                )
            ).decode('utf-8')

            # Delete the key pair after so that it can't be reused
            del self.key_pairs[ip]

            # Check if received data is valid
            if len(decrypted_content) != 64:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST('Invalid token format'))

            return decrypted_content

        return False


    # Use this to retrieve a public key from the server, and encrypt & return the content
    def public_encrypt(self, ip: str, port: int, content: str or int) -> dict:
        content = str(content)

        # Retrieve public key PEM and convert it back to a Python object
        pem = requests.get(f"http://{ip}:{port}/telepath/get_public_key").json()
        public_key = serialization.load_pem_public_key(
            pem.encode('utf-8'),
            backend=default_backend()
        )

        # Return content encrypted with the public key
        cipher_text = public_key.encrypt(
            content.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=self.sha256),
                algorithm=self.sha256,
                label=None
            )
        )
        return {'token': base64.b64encode(cipher_text).decode()}

# Handles reading and writing from telepath-secrets
class SecretHandler():

    def __init__(self):
        self.file = constants.telepathSecrets

        # Create a fernet key from the hardware ID
        key = hashlib.sha256(UNIQUE_ID.encode()).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key).decode('utf-8'))

    def _encrypt(self, data: str):
        return self.fernet.encrypt(data.encode('utf-8'))

    def _decrypt(self, data: bytes):
        try:
            return self.fernet.decrypt(data)
        except:
            print("[INFO] [telepath] Failed to load telepath-secrets, resetting...")
            return []

    def read(self):
        if os.path.exists(self.file):
            with open(self.file, 'rb') as f:
                content = f.read()
                decrypted = self._decrypt(content)
                try:
                    return json.loads(decrypted)
                except:
                    pass
        return []

    def write(self, data: list):
        if not os.path.exists(self.file):
            constants.folder_check(constants.telepathDir)

        if data:
            encrypted = self._encrypt(json.dumps(data))
        else:
            encrypted = self._encrypt('{}')

        with open(self.file, 'wb') as f:
            f.write(encrypted)

class AuditLogger():
    def __init__(self):
        self.path = os.path.join(constants.telepathDir, 'Logs')
        self.current_user = None
        self.max_logs = 50
        self.tags = {
            'ignore': ['_sync_attr'],
            'auth': ['login', 'logout', 'get_public_key', 'request_pair', 'confirm_pair'],
            'warn': ['save', 'restore'],
            'high': ['delete', 'import_script', 'script_state']
        }

    # Purge old logs
    def _purge_logs(self):
        file_data = {}
        for file in glob(os.path.join(self.path, "audit-*.log")):
            file_data[file] = os.stat(file).st_mtime

        sorted_files = sorted(file_data.items(), key=itemgetter(1))

        delete = len(sorted_files) - self.max_logs
        for x in range(0, delete):
            os.remove(sorted_files[x][0])

    # Returns formatted name of file, with the date
    def _get_file_name(self):
        time_stamp = dt.now().strftime(constants.fmt_date("%#m-%#d-%y"))
        return os.path.abspath(os.path.join(self.path, f"audit_{time_stamp}.log"))

    # Used for reporting internal events to self.log() and tagging them
    def _report(self, event: str, user: str = '', extra_data: str = ''):
        date_label = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
        event_tag = 'info'
        for t, events in self.tags.items():
            for e in events:
                if event.endswith(e.lower()):
                    if t == 'ignore':
                        return
                    else:
                        event_tag = e
                        break

        print(event_tag, date_label, user, event, extra_data)


    # Format list of dictionaries for UI
    def read(self):
        log_data = []
        file_name = self._get_file_name()
        if os.path.exists(file_name):
            with open(file_name, 'r') as f:
                log_data = f.readlines()
        return log_data

    # tag = ["info", "auth", "warn", "high"]
    def log(self, message: str, tag='info'):
        file_name = self._get_file_name()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str
    host_ip: str

auth_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: td = None):
    to_encode = data.copy()
    if expires_delta:
        expire = dt.now(tz.utc) + expires_delta
    else:
        expire = dt.now(tz.utc) + td(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate(token: str = Depends(auth_scheme), request: Request = None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        ip = request.client.host
        current_user = constants.api_manager.current_user

        # Only allow if machine name matches current user, and the IP is from the same location
        if payload.get('host') == current_user['host'] and ip == current_user['ip']:
            return True
    except InvalidTokenError:
        pass
    except KeyError:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )



# ---------------------------------------------- Utility Functions -----------------------------------------------------

# Creates an endpoint from a method, tagged, and optionally if it contains parameters, or requires a JWT token
def create_endpoint(method: Callable, tag: str, params=False, auth_required=True):
    kwargs = {
        'methods': ["POST" if params else "GET"],
        'name': method.__name__,
        'tags': [tag],
    }
    if auth_required:
        kwargs['dependencies'] = [Depends(authenticate)]

    app.add_api_route(
        f"/{tag}/{method.__name__}",
        return_endpoint(method, create_pydantic_model(method) if params else None),
        **kwargs
    )


# Reconstructs a serialized object to "__reconstruct__"
def reconstruct_object(data: dict):
    final_data = data
    if isinstance(data, dict):
        if '__reconstruct__' in data:
            if data['__reconstruct__'] == 'RemoteBackupObject':
                final_data = RemoteBackupObject(data['_telepath_data'], data)

            if data['__reconstruct__'] == 'RemoteAddonFileObject':
                final_data = RemoteAddonFileObject(data['_telepath_data'], data)

            if data['__reconstruct__'] == 'RemoteAddonWebObject':
                final_data = RemoteAddonWebObject(data['_telepath_data'], data)

            if data['__reconstruct__'] == 'RemoteAmsFileObject':
                final_data = RemoteAmsFileObject(data['_telepath_data'], data)

            if data['__reconstruct__'] == 'RemoteAmsWebObject':
                final_data = RemoteAmsWebObject(data['_telepath_data'], data)

    return final_data


# Returns {param: (type, Ellipsis or default value)} from the parameters of any function
def get_function_params(method: Callable):
    parameters = inspect.signature(method).parameters

    if not parameters or ("self" in parameters and len(parameters) == 1):
        return None

    def get_default_value(param):
        return ... if param.default is inspect._empty else param.default

    def get_param_type(param):
        final_type = str
        if 'Object' in param.annotation.__name__:
            final_type = object
        elif param.annotation != inspect._empty:
            final_type = param.annotation
        if final_type == str:
            if param.default != inspect._empty:
                final_type = type(param.default)
        return final_type

    return {
        param.name.strip('_'): (
            get_param_type(param),
            get_default_value(param),
        )
        for param in parameters.values()
        if param.name not in ["self", "args"]
    }


# noinspection PyTypeChecker
def create_pydantic_model(method: Callable) -> Optional[BaseModel]:
    fields = get_function_params(method)
    if not fields:
        return None

    model = create_model(
        f"{method.__name__}Input",
        __config__=type("Config", (), {"arbitrary_types_allowed": True}),
        **fields,
    )
    return model


# Create an endpoint from a function
def return_endpoint(func: Callable, input_model: Optional[BaseModel] = None):
    async def endpoint(input: input_model = Body(...) if input_model else None):
        if input_model:
            result = func(**input.dict())
        else:
            result = func()
        return result

    return endpoint


# Generate endpoints from all instance methods
def generate_endpoints(app: FastAPI, instance):

    # Loop over instance to create endpoints from each method
    for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
        if not name.endswith("__"):
            input_model = create_pydantic_model(instance._arg_map[name])
            endpoint = return_endpoint(method, input_model)
            response_model = get_type_hints(method).get("return", None)
            app.add_api_route(
                f"/{instance._obj_name}/{name}",
                endpoint,
                methods=["POST" if input_model else "GET"],
                response_model=response_model,
                name=name,
                tags=[instance._obj_name],
                dependencies=[Depends(authenticate)]
            )



# -------------------------------------------- Remote Server Wrapper ---------------------------------------------------

# This will communicate with the endpoints
# "request" parameter is in context to this particular session, or subjectively, "am I requesting data?"
def api_wrapper(self, obj_name: str, method_name: str, request=True, params=None, *args, **kwargs):
    def format_args():
        formatted = {}
        args_list = list(args)
        param_keys = list(params.keys())

        # Convert *args to corresponding parameters
        for i, arg in enumerate(args_list):
            if i < len(param_keys):
                key = param_keys[i]
                data_type, _ = params[key]
                formatted[key] = arg if (data_type == object or data_type.__name__ == 'NoneType') else data_type(arg)

        # Process **kwargs and overwrite any conflicts
        for key, value in kwargs.items():
            if key in params:
                data_type, _ = params[key]
                formatted[key] = data_type(value)

        return formatted
    operation = 'Requesting' if request else 'Responding to'

    if not constants.headless:
        print(f"[INFO] [telepath] {operation} API method '{obj_name}.{method_name}' with args: {args} and kwargs: {kwargs}")


    # If this session is requesting data from a remote session
    if request:
        data = self._telepath_data
        return constants.api_manager.request(
            endpoint=f'{obj_name}/{method_name}',
            host=data['host'],
            port=data['port'],
            args=(format_args() if params else None)
        )


    # If this session is responding to a remote request
    else:
        # Reconstruct data if available
        if isinstance(kwargs, dict):
            kwargs = {k: reconstruct_object(v) for k, v in kwargs.items()}

        # Manipulate strings to execute a function call to the actual server manager
        lookup = {'AclManager': 'acl', 'AddonManager': 'addon', 'ScriptManager': 'script_manager', 'BackupManager': 'backup'}
        command = 'returned = server_manager.remote_server.'
        short_name = ''
        if obj_name in lookup:
            identifier = lookup[obj_name]
            command += f'{short_name}.'
        command += f'{method_name}'

        # Format locals() to include a new "returned" variable which will store the data to be returned
        exec_memory = {'locals': {'returned': None}, 'globals': {'server_manager': constants.server_manager}}
        exec(command, exec_memory['globals'], exec_memory['locals'])

        # Report event to logger
        formatted_args = ''
        if kwargs:
            formatted_args = ', '.join([f'{k}: {v}' for k, v in kwargs.items()])
        constants.api_manager.logger._report(f'{short_name}.{method_name}', extra_data=formatted_args)

        return exec_memory['locals']['returned'](**kwargs)


# Creates a thin wrapper of obj where all methods point to api_wrapper
# "request" parameter is in context to this particular session, or subjectively, "am I requesting data?"
def create_remote_obj(obj: object, request=True):
    global app

    # Restrict methods from being remotely accessible
    endpoint_blacklist = ['set_directory']

    # Replace methods
    def __getattr__(self, name):

        # Attribute hard overrides
        if name.endswith('__'):
            return
        if name == 'run_data':
            return self._telepath_run_data()
        if name == 'crash_log':
            return self._sync_telepath_stop()['crash']


        try:
            # First, check if cache exists and is not expired
            if self._attr_cache and self._attr_cache['__expire__']:
                if self._attr_cache['__expire__'] < dt.now():
                    self._attr_cache = {}

            # If cache does not exist, grab everything and set expiry
            if not self._attr_cache:
                for k, v in self._request_attr('__all__').items():
                    v = self._override_attr(k, v)
                    self._attr_cache[k] = {'value': v, 'expire': self._reset_expiry()}
                return self._attr_cache[name]['value']

            # If cache exists and is not expired, use that
            if name in self._attr_cache and self._attr_cache[name]['expire']:
                if self._attr_cache[name]['expire'] > dt.now():
                    return self._attr_cache[name]['value']
                else:
                    self._attr_cache[name]['expire'] = None

            # If cache exists and is expired, get name, update cache, and reset expired
            return self._refresh_attr(name)

        except Exception as e:
            if constants.debug:
                print(f'Error (telepath): failed to fetch attribute, {e}')
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    def __setattr__(self, attribute, value):
        blacklist = ['_telepath_data', 'addon', 'acl', 'backup', 'script_manager']
        if self._attr_cache and attribute not in blacklist and not attribute.endswith('__'):
            self._attr_cache[attribute] = {'value': value, 'expire': self._reset_expiry()}
        return object.__setattr__(self, attribute, value)

    # Override values to store in cache
    def _override_attr(self, k, v):
        class_name = self.__class__.__name__
        if class_name == 'RemoteServerObject':
            if k == 'config_file':
                return constants.reconstruct_config(v)
        elif class_name == 'RemoteAclManager':
            if k in ['list_items', 'displayed_rule']:
                return self._reconstruct_list(v)
        elif class_name == 'RemoteAddonManager':
            if k in ['installed_addons']:
                return self._reconstruct_list(v)
        return v
    def _refresh_attr(self, name):
        response = self._override_attr(name, self._request_attr(name))
        self._attr_cache[name] = {'value': response, 'expire': self._reset_expiry(response)}
        return response
    def _request_attr(self, name):
        return api_wrapper(
            self,
            self._obj_name,
            '_sync_attr',
            True,
            {'name': (str, ...)},
            name
        )
    def _reset_expiry(self, value=None, length=60):
        if value == 'run_data':
            length = 1
        expiry = dt.now() + td(seconds=length)
        self._attr_cache['__expire__'] = expiry
        return expiry
    def _clear_attr_cache(self, name=None):
        if name:
            self._attr_cache[name]['expire'] = None
        else:
            self._attr_cache = {}

    # First, sort through all the attributes and methods
    data = {
        'attributes': {
            '_obj_name': obj.__name__,
            '_arg_map': {},
            '_func_list': [],
            '_attr_cache': {}
        },
        'methods': {
            '__getattr__': __getattr__,
            '__setattr__': __setattr__,
            '_override_attr': _override_attr,
            '_refresh_attr': _refresh_attr,
            '_request_attr': _request_attr,
            '_reset_expiry': _reset_expiry,
            '_clear_attr_cache': _clear_attr_cache
        } if request else {}
    }

    for method in dir(obj):
        name = str(method)
        if name in endpoint_blacklist:
            continue


        # If 'i' is a method, but not __magic__
        if callable(type(method)):
            if name.endswith('__'):
                continue

            attr = getattr(obj, name, None)
            params = get_function_params(attr)


            # Define a wrapper that takes 'self' and calls the original method
            def param_wrapper(func_name, func_params):
                def method_wrapper(self, *args, **kwargs):
                    return api_wrapper(self, self._obj_name, func_name, request, func_params, *args, **kwargs)
                return method_wrapper

            data['methods'][name] = param_wrapper(name, params)
            data['attributes']['_arg_map'][name] = attr
            data['attributes']['_func_list'].append(name)


        # If 'i' is an attribute
        else:
            data['attributes'][name] = None


    # Return new wrapper class
    return type(
        f'Remote{obj.__name__}',
        (),
        {**data['attributes'], **data['methods']}
    )


# Create objects to import for the rest of the app to request data
class RemoteServerObject(create_remote_obj(ServerObject)):

    def __init__(self, telepath_data: dict):
        self._telepath_data = telepath_data

        # Set display name
        if self._telepath_data['nickname']:
            self._telepath_data['display-name'] = self._telepath_data['nickname']
        else:
            self._telepath_data['display-name'] = self._telepath_data['host']
        self._view_name = f"{self._telepath_data['display-name']}/{self._telepath_data['name']}"
        self.favorite = self._is_favorite()

        self.run_data = {}
        self.backup = RemoteBackupManager(self)
        self.addon = RemoteAddonManager(self)
        self.acl = RemoteAclManager(self)
        self.script_manager = RemoteScriptManager(self)
        self._clear_all_cache()

        host = self._telepath_data['nickname'] if self._telepath_data['nickname'] else self._telepath_data['host']

        if not constants.headless:
            print(f"[INFO] [auto-mcs] Server Manager (Telepath): Loaded '{host}/{self.name}'")

    def _is_favorite(self):
        try:
            telepath = constants.server_manager.telepath_servers[self._telepath_data['host']]
            if self.name in telepath['added-servers']:
                return telepath['added-servers'][self.name]['favorite']
        except KeyError:
            pass
        return False

    def _clear_all_cache(self):
        self._clear_attr_cache()
        self.backup._clear_attr_cache()
        self.addon._clear_attr_cache()
        self.acl._clear_attr_cache()
        self.script_manager._clear_attr_cache()

    # Gather remote run_data from a running server
    def _telepath_run_data(self):
        run_data = super()._telepath_run_data()
        if run_data:
            run_data['send-command'] = self.send_command
            add_list = ['process-hooks', 'command-history']

            # Add missing keys for client-side additions
            for key in add_list:
                if key not in self.run_data:
                    run_data[key] = []

            # Fill in remote details to local run_data
            for k, v in run_data.items():
                self.run_data[k] = v

            return self.run_data

        else:
            self._clear_all_cache()
            return {}

    def _sync_telepath_stop(self):
        if self.run_data:
            self.run_data = {}
            self._clear_all_cache()
        return super()._sync_telepath_stop()

    def reload_config(self, *args, **kwargs):
        self._clear_all_cache()
        return super().reload_config(*args, **kwargs)

    def write_config(self):
        data = super().write_config(
            remote_data={
                'config_file': constants.reconstruct_config(self.config_file, to_dict=True),
                'server_properties': self.server_properties
            }
        )
        self._clear_all_cache()
        self.properties_hash = self._get_properties_hash()
        return data

    def launch(self, *args, **kwargs):
        self._clear_all_cache()
        super().launch(return_telepath=True, *args, **kwargs)
        return self._telepath_run_data()

    def send_command(self, *args, **kwargs):
        super().send_command(*args, **kwargs)
        def update_console(*a):
            self._telepath_run_data()
            for hook in self.run_data['process-hooks']:
                hook(self.run_data['log'])
        threading.Timer(0.1, update_console).start()

    def performance_stats(self, interval=0.5, update_players=False):
        if self.run_data and 'performance' in self.run_data:
            return self.run_data['performance']
        else:
            return {}

    def enable_auto_update(self, *args, **kwargs):
        data = super().enable_auto_update(*args, **kwargs)
        self._clear_attr_cache()
        return data

    # Shows taskbar notifications
    def _view_notif(self, name, add=True, viewed=''):
        if name and add:
            show_notif = name not in self.viewed_notifs
            if name in self.viewed_notifs:
                show_notif = viewed != self.viewed_notifs[name]

            if self.taskbar and show_notif:
                self.taskbar.show_notification(name)

            if name in self.viewed_notifs:
                if viewed:
                    self.viewed_notifs[name] = viewed
            else:
                self.viewed_notifs[name] = viewed

        elif (not add) and (name in self.viewed_notifs):
            del self.viewed_notifs[name]

        super()._view_notif(name, add, viewed)

    # Check if remote instance is not currently being blocked by a synchronous activity (update, create, restore, etc.)
    # Returns True if available
    def progress_available(self):
        return not constants.api_manager.request(
            endpoint='/main/get_remote_var',
            host=self._telepath_data['host'],
            port=self._telepath_data['port'],
            args={'var': 'ignore_close'}
        )

class RemoteScriptManager(create_remote_obj(ScriptManager)):
    def __init__(self, server_obj: RemoteServerObject):
        self._telepath_data = server_obj._telepath_data
        self.parent = server_obj

    def _reconstruct_list(self, script_list: dict):
        return {
            'enabled': [RemoteAmsFileObject(self._telepath_data, script) for script in script_list['enabled']],
            'disabled': [RemoteAmsFileObject(self._telepath_data, script) for script in script_list['disabled']]
        }

    def _enumerate_scripts(self):
        self._clear_attr_cache()
        return super()._enumerate_scripts()

    def return_single_list(self):
        try:
            return [RemoteAmsFileObject(self._telepath_data, data) for data in super().return_single_list()]
        except AttributeError:
            return []

    def search_scripts(self, query: str):
        return [RemoteAmsWebObject(self._telepath_data, data) for data in super().search_scripts(query)]

    def get_script(self, script_name: str, online=False):
        return [
            RemoteAddonWebObject(self._telepath_data, data) if online else
            RemoteAddonFileObject(self._telepath_data, data)
            for data in super().get_script(script_name, online)
        ]

    def import_script(self, script_path: str):
        data = super().import_script(constants.telepath_upload(self._telepath_data, script_path)['path'])
        constants.api_manager.request(endpoint='/main/clear_uploads', host=self._telepath_data['host'], port=self._telepath_data['port'])
        return RemoteAmsFileObject(self._telepath_data, data)

    def script_state(self, *args, **kwargs):
        self._clear_attr_cache()
        super().script_state(*args, **kwargs)

class RemoteAddonManager(create_remote_obj(AddonManager)):
    def __init__(self, server_obj: RemoteServerObject):
        self._telepath_data = server_obj._telepath_data
        self.parent = server_obj

    def _reconstruct_list(self, addon_list: dict):
        return {
            'enabled': [RemoteAddonFileObject(self._telepath_data, addon) for addon in addon_list['enabled']],
            'disabled': [RemoteAddonFileObject(self._telepath_data, addon) for addon in addon_list['disabled']]
        }

    def _refresh_addons(self):
        self._clear_attr_cache()
        return super()._refresh_addons()

    def return_single_list(self):
        try:
            return [RemoteAddonFileObject(self._telepath_data, data) for data in super().return_single_list()]
        except AttributeError:
            return []

    def search_addons(self, query: str, *args):
        return [RemoteAddonWebObject(self._telepath_data, data) for data in super().search_addons(query)]

    def get_addon(self, addon_name: str, online=False):
        return [
            RemoteAddonWebObject(self._telepath_data, data) if online else
            RemoteAddonFileObject(self._telepath_data, data)
            for data in super().get_addon(addon_name, online)
        ]

    def import_addon(self, addon_path: str):
        data = super().import_addon(constants.telepath_upload(self._telepath_data, addon_path)['path'])
        constants.api_manager.request(endpoint='/main/clear_uploads', host=self._telepath_data['host'], port=self._telepath_data['port'])
        return RemoteAddonFileObject(self._telepath_data, data)

    def addon_state(self, *args, **kwargs):
        self._clear_attr_cache()
        super().addon_state(*args, **kwargs)

class RemoteBackupManager(create_remote_obj(BackupManager)):
    def __init__(self, server_obj: RemoteServerObject):
        self._telepath_data = server_obj._telepath_data
        self.parent = server_obj

    def _update_data(self):
        self._clear_attr_cache()
        return super()._update_data()

    def return_backup_list(self):
        return [RemoteBackupObject(self._telepath_data, data) for data in super().return_backup_list()]

    def save(self, *args, **kwargs):
        data = super().save(*args, **kwargs)
        self._clear_attr_cache()
        return data

class RemoteAclManager(create_remote_obj(AclManager)):
    def __init__(self, server_obj: RemoteServerObject):
        self._telepath_data = server_obj._telepath_data
        self.parent = server_obj

    # Reconstruct AclRule objects from a dictionary representing a rule, or rule list(s)
    def _reconstruct_list(self, rule_list: dict):
        def create_rule(rule_data):
            rule = AclRule(
                rule_data['rule'],
                rule_data['acl_group'],
                bool(rule_data['rule_scope'] == 'global'),
                rule_data['extra_data']
            )
            rule.display_data = rule_data['display_data']
            rule.list_enabled = rule_data['list_enabled']
            return rule

        if isinstance(rule_list, dict):

            # Convert single rule
            if 'rule' in rule_list:
                return create_rule(rule_list)

            # Convert single list
            elif 'enabled' in rule_list and 'disabled' in rule_list:
                return {enabled: [create_rule(r) for r in rules] for enabled, rules in rule_list.items()}

            # Convert rule lists
            elif 'ops' in rule_list or 'wl' in rule_list or 'bans' in rule_list:
                is_sorted = False
                try:
                    is_sorted = isinstance(list(rule_list.values())[0], dict)
                except:
                    pass

                # Convert sorted menu list
                if is_sorted:
                    return {
                        list_type: {
                            'enabled': [create_rule(rule) for rule in rules['enabled']],
                            'disabled': [create_rule(rule) for rule in rules['disabled']]
                        } for list_type, rules in rule_list.items()
                    }

                # Convert unsorted menu list
                else:
                    return {
                        list_type: [create_rule(rule) for rule in rules]
                        for list_type, rules in rule_list.items()
                    }

        return rule_list

    def _gen_list_items(self):
        self._clear_attr_cache()
        return self._reconstruct_list(super()._gen_list_items())

    def get_rule(self, *args, **kwargs):
        self._clear_attr_cache()
        return self._reconstruct_list(super().get_rule(*args, **kwargs))

    def op_player(self, *args, **kwargs):
        self._clear_attr_cache()
        return self._reconstruct_list(super().op_player(*args, **kwargs))

    def ban_player(self, *args, **kwargs):
        self._clear_attr_cache()
        return self._reconstruct_list(super().ban_player(*args, **kwargs))

    def whitelist_player(self, *args, **kwargs):
        self._clear_attr_cache()
        return self._reconstruct_list(super().whitelist_player(*args, **kwargs))

    def enable_whitelist(self, enabled=True):
        data = super().enable_whitelist(enabled)
        self._refresh_attr('_server')
        return data

    def add_global_rule(self, *args, **kwargs):
        self._clear_attr_cache()
        return self._reconstruct_list(super().add_global_rule(*args, **kwargs))

class RemoteObject(Munch):
    def __init__(self, telepath_data, data: dict):
        self._telepath_data = data
        self.__reconstruct__ = self.__class__.__name__

        for key, value in data.items():
            if not key.endswith('__'):
                setattr(self, key, value)

class RemoteBackupObject(RemoteObject):
    pass
class RemoteAddonFileObject(RemoteObject):
    pass
class RemoteAddonWebObject(RemoteObject):
    pass
class RemoteAmsFileObject(RemoteObject):
    pass
class RemoteAmsWebObject(RemoteObject):
    pass



# ----------------------------------------------- API Endpoints --------------------------------------------------------

# API endpoints for authentication
# Keep-alive, unauthenticated
@app.get('/telepath/check_status', tags=['telepath'])
async def check_status():
    return True

# Retrieve the server's public key to encrypt and send the token
@app.get('/telepath/get_public_key', tags=['telepath'])
async def get_public_key(request: Request):
    if constants.api_manager:
        return constants.api_manager.auth._get_public_key(request.client.host)

    else:
        raise HTTPException(status_code=status.HTTP_425_TOO_EARLY, detail='Telepath is still initializing')

# Pair and authentication
@app.post("/telepath/request_pair", tags=['telepath'])
async def request_pair(host: dict, id_hash: dict, request: Request):
    if constants.api_manager:
        if 'token' in id_hash:
            id_hash = id_hash['token']

        # Check token length
        if len(id_hash) != 344:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST('Invalid token format'))

        # Report event to logger
        extra_data = 'Requested to pair'
        host['ip'] = request.client.host
        constants.api_manager.logger._report('telepath.request_pair', host=host, extra_data=extra_data)

        return constants.api_manager._request_pair(host, id_hash, request)

    else:
        raise HTTPException(status_code=status.HTTP_425_TOO_EARLY, detail='Telepath is still initializing')

@app.post("/telepath/submit_pair", tags=['telepath'])
async def submit_pair(host: dict, id_hash: dict, code: str, request: Request):
    if constants.api_manager:
        if 'token' in id_hash:
            id_hash = id_hash['token']

        # Check token length
        if len(id_hash) != 344:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST('Invalid token format'))

        data = constants.api_manager._submit_pair(host, id_hash, code, request)

        # Report event to logger
        host['ip'] = request.client.host
        extra_data = "Successfully authenticated" if data else "Failed to authenticate"
        constants.api_manager.logger._report('telepath.submit_pair', host=host, extra_data=extra_data)

        return data

    else:
        raise HTTPException(status_code=status.HTTP_425_TOO_EARLY, detail='Telepath is still initializing')

@app.post("/telepath/login", tags=['telepath'])
async def login(host: dict, id_hash: dict, request: Request):
    if constants.api_manager:
        if 'token' in id_hash:
            id_hash = id_hash['token']

        # Check token length
        if len(id_hash) != 344:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST('Invalid token format'))

        data = constants.api_manager._login(host, id_hash, request)

        # Report event to logger
        host['ip'] = request.client.host
        extra_data = "Successfully authenticated" if data else "Failed to authenticate"
        constants.api_manager.logger._report('telepath.login', host=host, extra_data=extra_data)

        return data

    else:
        raise HTTPException(status_code=status.HTTP_425_TOO_EARLY, detail='Telepath is still initializing')

@app.post("/telepath/logout", tags=['telepath'], dependencies=[Depends(authenticate)])
async def logout(host: dict, request: Request):
    if constants.api_manager:

        # Report event to logger
        constants.api_manager.logger._report('telepath.logout')

        return constants.api_manager._logout(host, request)

    else:
        raise HTTPException(status_code=status.HTTP_425_TOO_EARLY, detail='Telepath is still initializing')



# Authenticated and functional endpoints
@app.post("/main/open_remote_server", tags=['main'], dependencies=[Depends(authenticate)])
async def open_remote_server(name: str):
    if constants.app_config.telepath_settings['enable-api'] and constants.server_manager:
        return constants.server_manager.open_remote_server(name)

    # Report event to logger
    constants.api_manager.logger._report('main.open_remote_server', extra_data=f'Opened: "{name}"')

    return False

# Upload file endpoint
@app.post("/main/upload_file", tags=['main'], dependencies=[Depends(authenticate)])
async def upload_file(file: UploadFile = File(...), is_dir=False):
    if isinstance(is_dir, str):
        is_dir = is_dir.lower() == 'true'

    try:
        file_name = file.filename
        content_type = file.content_type
        file_content = await file.read()
        destination_path = os.path.join(constants.uploadDir, file_name)

        # Ensure directory exists
        os.makedirs(constants.uploadDir, exist_ok=True)

        with open(destination_path, "wb") as f:
            f.write(file_content)

        if is_dir:
            dir_name = file_name if '.' not in file_name else file_name.rsplit('.', 1)[0]
            constants.extract_archive(destination_path, constants.uploadDir)
            os.remove(destination_path)
            destination_path = os.path.join(constants.uploadDir, dir_name)

        # Report event to logger
        constants.api_manager.logger._report('main.upload_file', extra_data=f'Uploaded: "{destination_path}"')

        return JSONResponse(content={
            "name": file_name,
            "path": destination_path,
            "content_type": content_type
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# Download file endpoint
@app.post("/main/download_file", tags=['main'], dependencies=[Depends(authenticate)])
async def download_file(file: str):
    denied = HTTPException(status_code=403, detail=f"Access denied")
    blocked_symbols = ['*', '..']

    # First, normalize path to current OS
    if constants.os_name == 'windows':
        path = os.path.normpath(file).replace('/', '\\')
    else:
        path = os.path.normpath(file).replace('\\', '/')


    # Block directory traversal
    for s in blocked_symbols:
        if s in path:
            raise denied

    # Prevent downloading files from outside permitted paths, and permitted names
    for p in constants.telepath_download_whitelist['paths']:
        if path.startswith(p):
            break
    else:
        raise denied

    # Prevent downloading files without permitted names
    for n in constants.telepath_download_whitelist['names']:
        if path.endswith(n):
            break
    else:
        raise denied

    # If the file resides in a permitted directory, check if it actually exists
    if not os.path.isfile(path):
        raise HTTPException(status_code=500, detail=f"File '{file}' does not exist")

    # Report event to logger
    constants.api_manager.logger._report('main.download_file', extra_data=f'Downloaded: "{path}"')

    # If it exists in a permitted directory, respond with the file
    return FileResponse(path, filename=os.path.basename(path))

# Generate endpoints both statically & dynamically
[generate_endpoints(app, create_remote_obj(r, False)()) for r in
 (ServerObject, AmsFileObject, ScriptManager, AddonFileObject, AddonManager, BackupManager, AclManager)]

# General auto-mcs endpoints
create_endpoint(svrmgr.create_server_list, 'main')
create_endpoint(constants.make_update_list, 'main')
create_endpoint(constants.get_remote_var, 'main', True)
create_endpoint(constants.java_check, 'main', True)
create_endpoint(constants.allow_close, 'main', True)
create_endpoint(constants.clear_uploads, 'main')
create_endpoint(constants.update_world, 'main', True)

# Add-on based functionality outside the add-on manager
create_endpoint(constants.load_addon_cache, 'addon', True)
create_endpoint(constants.iter_addons, 'addon', True)
create_endpoint(constants.pre_addon_update, 'addon', True)
create_endpoint(constants.post_addon_update, 'addon', True)

# Endpoints for updating, server creation, and importing
create_endpoint(constants.push_new_server, 'create', True)
create_endpoint(constants.download_jar, 'create', True)
create_endpoint(constants.install_server, 'create', True)
create_endpoint(constants.generate_server_files, 'create', True)
create_endpoint(constants.update_server_files, 'create', True)
create_endpoint(constants.create_backup, 'create', True)
create_endpoint(constants.pre_server_update, 'create', True)
create_endpoint(constants.post_server_update, 'create', True)
create_endpoint(constants.pre_server_create, 'create', True)
create_endpoint(constants.post_server_create, 'create', True)

create_endpoint(constants.scan_import, 'create', True)
create_endpoint(constants.finalize_import, 'create', True)
create_endpoint(constants.scan_modpack, 'create', True)
create_endpoint(constants.finalize_modpack, 'create', True)
