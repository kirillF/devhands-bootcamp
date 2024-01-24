from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
import time
import ctypes
from datetime import datetime
from resource import getrusage, RUSAGE_SELF
import platform
from dotenv import load_dotenv
import psycopg
from psycopg import AsyncConnection
import aioredis
import os

load_dotenv()


origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_conn():
    pool = await psycopg.create_pool(
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
    )
    async with pool.acquire() as conn:
        yield conn


async def get_redis():
    host = os.getenv("REDIS_HOST")
    port = os.getenv("REDIS_PORT")
    redis = await aioredis.create_redis_pool(f"redis://{host}:{port}")
    return redis


if platform.system() == "MacOS":
    libc = ctypes.CDLL("libc.dylib")
elif platform.system() == "Linux":
    libc = ctypes.CDLL("libc.so.6")
else:
    libc = ctypes.CDLL(None)


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


@app.get("/warmup")
async def warmup(conn: AsyncConnection = Depends(get_conn)):
    for i in range(1, 6):
        item = await get_redis().get(f"item:{i}")
        if item is None:
            item = await read_item(i, conn)
            await get_redis().set(f"item:{i}", item)


@app.get("/items/{item_id}")
async def read_item(item_id: int, conn: AsyncConnection = Depends(get_conn)):
    item = await conn.fetchrow("SELECT * FROM items WHERE id = $1", item_id)
    return item


@app.get("/items")
async def read_items(conn: AsyncConnection = Depends(get_conn)):
    response = []
    for i in range(1, 6):
        result = await read_item(i, conn)
        response.append(result)
    return response


@app.get("/items/cache/{item_id}")
async def get_item_from_cache(item_id: int):
    item = await get_redis().get(f"item:{item_id}")
    return item


@app.get("/items/cache")
async def read_items_from_cache():
    redis = await get_redis()
    items = []
    for i in range(1, 6):  # Fetch items with IDs from 1 to 5
        item = await redis.get(f"item:{i}")
        items.append(item)
    return items
