# This file abstracts all the program managers to control a server remotely
# import sys
# sys.path.append('/')

from fastapi import FastAPI, Body
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, create_model
from typing import Callable, get_type_hints, Optional
from functools import partial
import threading
import requests
import asyncio
import inspect
import uvicorn

# Local imports
from svrmgr import ServerObject, ViewObject
from amscript import AmsFileObject, ScriptManager
from addons import AddonFileObject, AddonManager
from backup import BackupManager
from acl import AclManager
import constants



# Placeholder for authentication
def get_token():
    return 'token'


# This will communicate with the endpoints
# "request" parameter is in context to this particular session, or subjectively, "am I requesting data?"
def api_wrapper(obj_name: str, method_name: str, request=True, params=None, *args, **kwargs):
    def format_args():
        formatted = {}
        args_list = list(args)

        for key, (data_type, _) in params.items():
            if key in kwargs:
                formatted[key] = data_type(kwargs[key])
            elif args_list:
                formatted[key] = data_type(args_list.pop(0))
            else:
                # Skip assignment if the argument is missing
                continue

        return formatted

    operation = 'Requesting' if request else 'Responding to'
    print(f"{operation} API method '{obj_name}.{method_name}' with args: {args} and kwargs: {kwargs}")


    # If this session is requesting data from a remote session
    if request:
        url = f"http://localhost:8000/{obj_name}/{method_name}"
        headers = {
            "Authorization": f"Token {get_token()}",
            "Content-Type": "application/json",
        }

        # Determine POST or GET based on params
        data = requests.post(url, headers=headers, json=format_args()) if params else requests.get(url, headers=headers)
        return data



    # If this session is responding to a remote request
    else:

        # Manipulate strings to execute an function call to the actual server manager
        lookup = {'AclManager': 'acl', 'AddonManager': 'addon', 'ScriptManager': 'script_manager', 'BackupManager': 'backup'}
        args = ', '.join([f"{key}='{value}'" for key, value in kwargs.items()])
        command = f'returned = constants.server_manager.current_server.'
        if obj_name in lookup:
            command += f'{lookup[obj_name]}.'
        command += f'{method_name}({args})'
        # print(command)

        # Format locals() to include a new "returned" variable which will store the data to be returned
        local_data = locals()
        local_data['returned'] = None
        exec(command, globals(), local_data)

        return local_data['returned']


# Creates a wrapper clone of obj where all methods point to api_wrapper
# "request" parameter is in context to this particular session, or subjectively, "am I requesting data?"
def create_remote(obj: object, request=True):
    global app

    # First, sort through all the attributes and methods
    data = {'attributes': {'_obj_name': obj.__name__, '_arg_map': {}}, 'methods': {}}

    for method in dir(obj):
        name = str(method)

        # If 'i' is a method, but not __magic__
        if callable(type(method)):
            if name.endswith('__'):
                continue

            attr = getattr(obj, name, None)
            params = get_function_params(attr)

            data['methods'][name] = partial(api_wrapper, obj.__name__, name, request, params)
            data['attributes']['_arg_map'][name] = attr


        # If 'i' is an attribute
        else:
            data['attributes'][name] = None


    # Return new wrapper class
    return type(
        f'Remote{obj.__name__}',
        (),
        {**data['attributes'],
         **data['methods']}
    )


# Returns {param: type} from the parameters of any function
def get_function_params(method: Callable):
    parameters = inspect.signature(method).parameters

    if not parameters or ("self" in parameters and len(parameters) == 1):
        return None
    return {
        param.name: (
            object if 'Object' in param.annotation.__name__ else param.annotation if param.annotation != inspect._empty else str,
            ...,
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


# Generate endpoints from all instance methods
def generate_endpoints(app: FastAPI, instance):

    # Create an endpoint from a function
    def create_endpoint(func: Callable, input_model: Optional[BaseModel] = None):
        async def endpoint(input: input_model = Body(...) if input_model else None):
            if input_model:
                result = func(**input.dict())
            else:
                result = func()
            return result

        return endpoint

    # Check if a function is a partial
    def is_partial(m):
        return isinstance(m, partial)

    # Convert partial to function
    def partial_to_function(partial):
        # Extract original function and its arguments
        func = partial.func
        args = partial.args
        keywords = partial.keywords

        # Create a new function with fixed arguments
        def new_func(*additional_args, **additional_kwargs):
            all_args = args + additional_args
            return func(*all_args, **keywords, **additional_kwargs)

        return new_func

    # Loop over instance to create endpoints from each method
    for name, method in inspect.getmembers(instance, predicate=is_partial):
        if not name.endswith("__"):
            method = partial_to_function(method)
            input_model = create_pydantic_model(instance._arg_map[name])
            endpoint = create_endpoint(method, input_model)
            response_model = get_type_hints(method).get("return", None)
            app.add_api_route(
                f"/{instance._obj_name}/{name}",
                endpoint,
                methods=["POST" if input_model else "GET"],
                response_model=response_model,
                name=name,
            )


# Generate OpenAPI schema
def create_schema():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="auto-mcs Web API",
        version=constants.api_version,
        summary="This is the auto-mcs Web API. Useful for interacting with the auto-mcs application remotely.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://github.com/macarooni-man/auto-mcs/blob/main/source/gui-assets/logo.png?raw=true"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Internal wrapper for API functionality
class WebAPI():
    def __init__(self, app: FastAPI, host: str, port: int):
        self.app = app
        self.config = None
        self.server = None
        self.running = False
        self.update_config(host=host, port=port)

    def update_config(self, host: str, port: int):
        self.config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            # workers=1,
            # limit_concurrency=1,
            # limit_max_requests=1
        )

    def run_uvicorn(self):
        self.server = uvicorn.Server(self.config)
        self.server.run()

    def start(self):
        if not self.running:
            self.running = True
            threading.Timer(0, self.run_uvicorn).start()

    def stop(self):
        # This still doesn't work for whatever reason?
        if self.running:
            self.server.force_exit = True
            asyncio.run(self.server.shutdown())
            self.server = None
            self.running = False


# Create objects to import for the rest of the app to request data
class RemoteServerObject(create_remote(ServerObject)):
    def __init__(self):
        self.backup = RemoteBackupManager()
        self.addon = RemoteAddonManager()
        self.acl = RemoteAclManager()
        self.script_manager = RemoteScriptManager()


RemoteViewObject = create_remote(ViewObject)
RemoteAmsFileObject = create_remote(AmsFileObject)
RemoteScriptManager = create_remote(ScriptManager)
RemoteAddonFileObject = create_remote(AddonFileObject)
RemoteAddonManager = create_remote(AddonManager)
RemoteBackupManager = create_remote(BackupManager)
RemoteAclManager = create_remote(AclManager)




# Instantiate the API, and create all the endpoints
app = FastAPI()
obj_list = (ServerObject, ViewObject, AmsFileObject, ScriptManager, AddonFileObject, AddonManager, BackupManager, AclManager)
remote_obj_list = [generate_endpoints(app, create_remote(r, False)()) for r in obj_list]
app.openapi = create_schema

constants.api_manager = WebAPI(app, '0.0.0.0', 8000)
constants.api_manager.start()
