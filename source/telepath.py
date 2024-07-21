# This file abstracts all the program managers to control a server remotely
# import sys
# sys.path.append('/')

from typing import Callable, get_type_hints, Optional
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, create_model
from fastapi import FastAPI, Body
from munch import Munch
import threading
import requests
import inspect
import uvicorn
import time

# Local imports
from amscript import AmsFileObject, ScriptManager
from addons import AddonFileObject, AddonManager
from backup import BackupManager
from svrmgr import ServerObject
from acl import AclManager
import constants
import svrmgr



# Placeholder for authentication
def get_token():
    return 'token'


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
                formatted[key] = arg if data_type == object else data_type(arg)

        # Process **kwargs and overwrite any conflicts
        for key, value in kwargs.items():
            if key in params:
                data_type, _ = params[key]
                formatted[key] = data_type(value)

        return formatted
    operation = 'Requesting' if request else 'Responding to'
    print(f"{operation} API method '{obj_name}.{method_name}' with args: {args} and kwargs: {kwargs}")


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

        # Manipulate strings to execute a function call to the actual server manager
        lookup = {'AclManager': 'acl', 'AddonManager': 'addon', 'ScriptManager': 'script_manager', 'BackupManager': 'backup'}
        command = 'returned = server_manager.remote_server.'
        if obj_name in lookup:
            command += f'{lookup[obj_name]}.'
        command += f'{method_name}'

        # Format locals() to include a new "returned" variable which will store the data to be returned
        exec_memory = {'locals': {'returned': None}, 'globals': {'server_manager': constants.server_manager}}
        exec(command, exec_memory['globals'], exec_memory['locals'])

        return exec_memory['locals']['returned'](**kwargs)


# Creates a wrapper clone of obj where all methods point to api_wrapper
# "request" parameter is in context to this particular session, or subjectively, "am I requesting data?"
def create_remote_obj(obj: object, request=True):
    global app

    # Replace magic methods
    def __getattr__(self, name):
        if name.endswith('__'):
            return
        try:
            response = api_wrapper(
                self,
                self._obj_name,
                '_sync_attr',
                True,
                {'name': (str, ...)},
                name
            )
            return response

        except:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


    # First, sort through all the attributes and methods
    data = {
        'attributes': {'_obj_name': obj.__name__, '_arg_map': {}, '_func_list': []},
        'methods': {'__getattr__': __getattr__} if request else {}
        # , '__init__': __init__
    }

    for method in dir(obj):
        name = str(method)

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


# Creates an endpoint from a method, tagged, and optionally if it contains parameters
def create_endpoint(method: Callable, tag: str, params=False):
    app.add_api_route(
        f"/{tag}/{method.__name__}",
        return_endpoint(method, create_pydantic_model(method) if params else None),
        methods=["POST" if params else "GET"],
        name=method.__name__,
        tags=[tag]
    )


# Reconstructs a serialized object to "__reconstruct__"
def reconstruct_object(data: dict):
    final_data = data
    print(True, 1)
    if '__reconstruct__' in data:
        print(True, 2)
        if data['__reconstruct__'] == 'RemoteBackupObject':
            final_data = RemoteBackupObject(data['_telepath_data',], data)
            print(final_data)

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
        param.name: (
            get_param_type(param),
            get_default_value(param),
        )
        for param in parameters.values()
        if param.name != "self"
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
                tags=[instance._obj_name]
            )


# Generate OpenAPI schema
def create_schema():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="auto-mcs - Telepath API",
        version=constants.api_data['version'],
        summary="Welcome to the auto-mcs Telepath API! You can use this utility for seamless remote management.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": constants.api_data['logo']
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Internal wrapper for API functionality
class WebAPI():
    def __init__(self, host: str, port: int):
        global app
        self.app = app
        self.config = None
        self.server = None
        self.running = False
        self.host = host
        self.port = port
        self.update_config(host=host, port=port)

    def _run_uvicorn(self):
        self.server = uvicorn.Server(self.config)
        self.server.run()

    def _kill_uvicorn(self):
        self.server.should_exit = True

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
            print(f'WebAPI: active on "{self.host}:{self.port}"')
            threading.Timer(0, self._run_uvicorn).start()

    def stop(self):
        # This still doesn't work for whatever reason?
        if self.running:
            self._kill_uvicorn()
            self.server = None
            self.running = False

    def restart(self):
        self.stop()
        time.sleep(1)
        self.start()

    # Send a POST or GET request to an endpoint
    def request(self, endpoint: str, host=None, port=None, args=None, timeout=1):
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        if endpoint.endswith('/'):
            endpoint = endpoint[:-1]
        if not host:
            host = self.host
        if not port:
            port = self.port

        url = f"http://{host}:{port}/{endpoint}"
        headers = {
            "Authorization": f"Token {get_token()}",
            "Content-Type": "application/json",
        }

        # Determine POST or GET based on params
        data = requests.post(url, headers=headers, json=args, timeout=timeout) if args is not None else requests.get(url, headers=headers, timeout=timeout)

        if not data:
            return None

        json_data = data.json()
        if isinstance(json_data, dict) and "__reconstruct__" in json_data:
            return reconstruct_object(json_data)

        return json_data


# Create objects to import for the rest of the app to request data
class RemoteServerObject(create_remote_obj(ServerObject)):

    def __init__(self, telepath_data: dict):
        self._telepath_data = telepath_data
        self.backup = RemoteBackupManager(telepath_data)
        self.addon = RemoteAddonManager(telepath_data)
        self.acl = RemoteAclManager(telepath_data)
        self.script_manager = RemoteScriptManager(telepath_data)

        host = self._telepath_data['nickname'] if self._telepath_data['nickname'] else self._telepath_data['host']
        print(f"[INFO] [auto-mcs] Server Manager (Telepathy): Loaded '{host}/{self.name}'")

    # Check if remote instance is not currently being blocked by a synchronous activity (update, create, restore, etc.)
    # Returns True if available
    def progress_available(self):
        return not constants.api_manager.request(
            endpoint='/main/get_remote_var',
            host=self._telepath_data['host'],
            port=self._telepath_data['port'],
            args={'var': 'ignore_close'}
        )


class RemoteAmsFileObject(create_remote_obj(AmsFileObject)):
    def __init__(self, telepath_data: dict):
        self._telepath_data = telepath_data

class RemoteScriptManager(create_remote_obj(ScriptManager)):
    def __init__(self, telepath_data: dict):
        self._telepath_data = telepath_data

class RemoteAddonFileObject(create_remote_obj(AddonFileObject)):
    def __init__(self, telepath_data: dict):
        self._telepath_data = telepath_data

class RemoteAddonManager(create_remote_obj(AddonManager)):
    def __init__(self, telepath_data: dict):
        self._telepath_data = telepath_data

class RemoteBackupManager(create_remote_obj(BackupManager)):
    def __init__(self, telepath_data: dict):
        self._telepath_data = telepath_data
    def return_backup_list(self):
        return [RemoteBackupObject(self._telepath_data, data) for data in super().return_backup_list()]

class RemoteBackupObject(Munch):
    def __init__(self, telepath_data: dict, backup_data: dict):
        super().__init__()
        self._telepath_data = telepath_data
        self.__reconstruct__ = self.__class__.__name__

        for key, value in backup_data.items():
            if not key.endswith('__'):
                setattr(self, key, value)

class RemoteAclManager(create_remote_obj(AclManager)):
    def __init__(self, telepath_data: dict):
        self._telepath_data = telepath_data



# Instantiate the API
def get_docs_url(type: str):
    if not constants.app_compiled:
        return "/docs" if "docs" in type else "/redoc"
app = FastAPI(docs_url=get_docs_url("docs"), redoc_url=get_docs_url("redoc"))
app.openapi = create_schema


# Generate endpoints both statically & dynamically
[generate_endpoints(app, create_remote_obj(r, False)()) for r in
 (ServerObject, AmsFileObject, ScriptManager, AddonFileObject, AddonManager, BackupManager, AclManager)]

create_endpoint(svrmgr.create_server_list, 'main')
create_endpoint(constants.get_remote_var, 'main', True)
create_endpoint(constants.java_check, 'main', True)
