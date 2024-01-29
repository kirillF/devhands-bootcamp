from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import ctypes
from resource import getrusage, RUSAGE_SELF
import platform
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool
import os
import math
import asyncio
import redis.asyncio as aioredis
from contextlib import asynccontextmanager


load_dotenv()


origins = ["*"]


conn_info = f'host={os.getenv("POSTGRES_HOST")} port={os.getenv("POSTGRES_PORT")} dbname={os.getenv("POSTGRES_DB")} user={os.getenv("POSTGRES_USER")} password={os.getenv("POSTGRES_PASSWORD")}'
host = os.getenv("REDIS_HOST")
port = os.getenv("REDIS_PORT")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.redis = await aioredis.from_url(
        f"redis://{host}:{port}", encoding="utf-8", decode_responses=True
    )
    app.async_pool = AsyncConnectionPool(conninfo=conn_info)
    yield
    await app.async_pool.close()
    await app.redis.close()


if platform.system() == "MacOS":
    libc = ctypes.CDLL("libc.dylib")
elif platform.system() == "Linux":
    libc = ctypes.CDLL("libc.so.6")
else:
    libc = ctypes.CDLL(None)

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
            k = (k + 1) % 1000000
            result += math.exp(math.sin(math.radians(k))) * math.log1p(k)
            curr = getrusage(RUSAGE_SELF).ru_utime
            if curr - start >= cpu / 1000:
                break
        end = getrusage(RUSAGE_SELF).ru_utime
        return {
            "duration": str(cpu) + "ms",
            "status": "ok",
            "start": start,
            "end": end,
        }

    async def _sleep(sleep):
        start = getrusage(RUSAGE_SELF).ru_utime
        asyncio.sleep(sleep / 1000)
        end = getrusage(RUSAGE_SELF).ru_utime
        return {
            "duration": str(sleep) + "ms",
            "status": "ok",
            "start": start,
            "end": end,
        }

    async def _usleep(usleep):
        start = getrusage(RUSAGE_SELF).ru_utime
        libc.usleep(usleep * 1000)
        end = getrusage(RUSAGE_SELF).ru_utime
        return {
            "duration": str(usleep) + "ms",
            "status": "ok",
            "start": start,
            "end": end,
        }

    if cpu > 0:
        cpu = await asyncio.create_task(cpu_abuse(cpu))
        response["cpu"] = cpu

    if sleep > 0:
        sleep = await asyncio.create_task(_sleep(sleep))
        response["sleep"] = sleep

    if usleep > 0:
        usleep = await asyncio.create_task(_usleep(usleep))
        response["usleep"] = usleep

    return response


@app.get("/warmup")
async def warmup(request: Request):
    r = request.app.redis
    async with request.app.async_pool.connection() as conn:
        for i in range(1, 6):
            item = await r.get(f"item:{i}")
            if item is None:
                item = db_item_to_dict(await read_item(i, conn))
                await r.set(f"item:{i}", str(item))


@app.get("/items/{item_id}")
async def read_item(item_id: int, request: Request, from_cache: bool = False):
    if from_cache:
        item = await request.app.redis.get(f"item:{item_id}")
        return item
    else:
        async with request.app.async_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"SELECT * FROM items WHERE id = {item_id}")
                item = await cur.fetchone()
                return item


@app.get("/items")
async def read_items(request: Request, from_cache: bool = False):
    response = []
    for i in range(1, 6):
        item = read_item(i, request, from_cache)
        response.append(item)
    return response


def db_item_to_dict(item):
    return {
        "id": item[0],
        "name": item[1],
        "description": item[2],
        "date": item[3],
    }
