from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
import sys
import time
import math
import ctypes
from datetime import datetime
import asyncio

origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/abuse")
async def abuse(cpu: int = 0, sleep: int = 0, blocking: bool = False):
    response = {}

    def fib(n):
        if n <= 1:
            return n
        else:
            return fib(n - 1) + fib(n - 2)

    async def cpu_abuse(cpu):
        start = time.time()
        fib_num = 20
        while time.time() - start < cpu / 1000:
            fib(fib_num)
        end = time.time()
        response["cpu"] = {
            "duration": str(cpu) + "ms",
            "status": "ok",
            "start": datetime.fromtimestamp(start),
            "end": datetime.fromtimestamp(end),
        }

    async def sleep_abuse(sleep, blocking):
        start = time.time()
        if blocking:
            time.sleep(sleep / 1000)
        else:
            await asyncio.sleep(sleep / 1000)
        end = time.time()
        response["sleep"] = {
            "duration": str(sleep) + "ms",
            "status": "ok",
            "start": datetime.fromtimestamp(start),
            "end": datetime.fromtimestamp(end),
        }

    if cpu > 0:
        await cpu_abuse(cpu)

    if sleep > 0:
        await sleep_abuse(sleep, blocking)

    return response


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}


@app.get("/users")
async def read_users():
    return ["Rick", "Morty"]


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]


@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str = None, short: bool = False):
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item
