from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
import sys
import time
import math
import ctypes
from datetime import datetime
import asyncio
from resource import getrusage, RUSAGE_SELF
import platform

origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if platform.system() == "MacOS":
    libc = ctypes.CDLL("libc.dylib")
elif platform.system() == "Linux":
    libc = ctypes.CDLL("libc.so.6")
else:
    libc = ctypes.CDLL(None)


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/abuse")
async def abuse(cpu: int = 0, sleep: int = 0, usleep: int = 0):
    response = {}

    def cpu_abuse(cpu):
        start = getrusage(RUSAGE_SELF).ru_utime
        result = 0
        k = 0
        while True:
            for i in range(k):
                for j in range(i):
                    result += (k**17 + i**13 + j**11) % (10**17 + 7)
            k = (k + 1) % (10**17 + 7)

            curr = getrusage(RUSAGE_SELF).ru_utime
            if curr - start >= cpu / 1000:
                break
        end = getrusage(RUSAGE_SELF).ru_utime
        response["cpu"] = {
            "duration": str(cpu) + "ms",
            "status": "ok",
            "start": start,
            "end": end,
        }

    if cpu > 0:
        cpu_abuse(cpu)

    if sleep > 0:
        start = getrusage(RUSAGE_SELF).ru_utime
        time.sleep(sleep / 1000)
        end = getrusage(RUSAGE_SELF).ru_utime
        response["sleep"] = {
            "duration": str(sleep) + "ms",
            "status": "ok",
            "start": start,
            "end": end,
        }

    if usleep > 0:
        start = getrusage(RUSAGE_SELF).ru_utime
        libc.usleep(usleep * 1000)
        end = getrusage(RUSAGE_SELF).ru_utime
        response["usleep"] = {
            "duration": str(usleep) + "ms",
            "status": "ok",
            "start": start,
            "end": end,
        }

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
