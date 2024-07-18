# This file abstracts all the program managers to control a server remotely
# import sys
# sys.path.append('/')


from fastapi import FastAPI, Body
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, create_model
from typing import Callable, get_type_hints, Optional
from functools import partial
import inspect

from svrmgr import ServerObject, ViewObject
from amscript import AmsFileObject, ScriptManager
from addons import AddonFileObject, AddonManager
from backup import BackupManager
from acl import AclManager
import constants


obj_list = (
    ServerObject,
    ViewObject,
    AmsFileObject,
    ScriptManager,
    AddonFileObject,
    AddonManager,
    BackupManager,
    AclManager
)


def create_endpoint(func: Callable, input_model: Optional[BaseModel] = None):
    async def endpoint(input: input_model = Body(...) if input_model else None):
        if input_model:
            result = func(**input.dict())
        else:
            result = func()
        return result

    return endpoint


# noinspection PyTypeChecker
def create_pydantic_model(method: Callable) -> Optional[BaseModel]:
    parameters = inspect.signature(method).parameters

    if not parameters or ("self" in parameters and len(parameters) == 1):
        return None
    fields = {
        param.name: (
            object if 'Object' in param.annotation.__name__ else param.annotation if param.annotation != inspect._empty else str,
            ...,
        )
        for param in parameters.values()
        if param.name != "self"
    }

    model = create_model(
        f"{method.__name__}Input",
        __config__=type("Config", (), {"arbitrary_types_allowed": True}),
        **fields,
    )
    return model


# This will communicate with the endpoints
def api_wrapper(obj_name, method_name: str, *args, **kwargs):
    print(f"Calling API method '{obj_name}.{method_name}' with args: {args} and kwargs: {kwargs}")
    lookup = {
        'AclManager': 'acl',
        'AddonManager': 'addon',
        'ScriptManager': 'script_manager',
        'BackupManager': 'backup',
    }

    args = ', '.join([f"{key}='{value}'" for key, value in kwargs.items()])
    command = f'constants.server_manager.current_server.'
    if obj_name in lookup:
        command += f'{lookup[obj_name]}.'
    command += f'{method_name}({args})'

    print(constants, command)
    exec(command, globals(), locals())

    # return endpoint_request(function, *args, **kwargs)
    pass


def generate_endpoints(app: FastAPI, instance):

    def is_partial(m):
        return isinstance(m, partial)

    # Function to convert partial to function
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



# Create a wrapper clone where all methods point to api_wrapper
def remote(obj: object):
    global app

    # First, sort through all the attributes and methods
    data = {'attributes': {'_obj_name': obj.__name__, '_arg_map': {}}, 'methods': {}}

    for method in dir(obj):
        name = str(method)

        # If 'i' is a method, but not __magic__
        if callable(type(method)):
            if name.endswith('__'):
                continue

            data['methods'][name] = partial(api_wrapper, obj.__name__, name)
            data['attributes']['_arg_map'][name] = getattr(obj, name, None)


        # If 'i' in an attribute
        else:
            data['attributes'][name] = None


    # Return new wrapper class
    return type(
        f'Remote{obj.__name__}',
        (),
        {**data['attributes'],
         **data['methods']}
    )








app = FastAPI()
remote_obj_list = [generate_endpoints(app, remote(r)()) for r in obj_list]

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="auto-mcs Web API",
        version="0.0.1",
        summary="This is the auto-mcs Web API. Useful for interacting with the auto-mcs application remotely.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://raw.githubusercontent.com/macarooni-man/auto-mcs/main/other/github-banner-cropped.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)

# r = remote(ServerObject)()
# r.launch('pp', lick_my='COCK')
