from fastapi import FastAPI, Body
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, create_model
from typing import Callable, get_type_hints, Optional
import inspect

""" 
This is an example Class for the endpoint generation. 
We need to replace this Class with the new ServerObject Class.
The goal of this is to have a starting point for the
decoupling of the UI from the Server logic.
TODO: Create a new RemoteServerObject Class
"""


class MyClass:
    def method_one(self, param: int) -> str:
        return f"Result of method_one with param: {param}"

    def method_two(self, param: str) -> str:
        return f"Result of method_two with param: {param}"

    def method_three(self) -> str:
        return "Result of method_three"


my_instance = MyClass()


def create_endpoint(func: Callable, input_model: Optional[BaseModel] = None):
    async def endpoint(input: input_model = Body(...) if input_model else None):
        if input_model:
            result = func(**input.dict())
        else:
            result = func()
        return result

    return endpoint


def create_pydantic_model(method: Callable) -> Optional[BaseModel]:
    parameters = inspect.signature(method).parameters
    if not parameters or ("self" in parameters and len(parameters) == 1):
        return None
    fields = {
        param.name: (
            param.annotation if param.annotation != inspect._empty else str,
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


def add_class_methods_to_routes(app: FastAPI, instance):
    for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
        if not name.startswith("_"):
            input_model = create_pydantic_model(method)
            endpoint = create_endpoint(method, input_model)
            response_model = get_type_hints(method).get("return", None)
            app.add_api_route(
                f"/{name}",
                endpoint,
                methods=["POST" if input_model else "GET"],
                response_model=response_model,
                name=name,
            )


app = FastAPI()
add_class_methods_to_routes(app, my_instance)


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
