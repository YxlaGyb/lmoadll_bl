# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0

from quart import Quart
from magic import Init_module
from dotenv import load_dotenv
import asyncio
import os

_ = load_dotenv()
app = Quart(__name__)
app.config["DEBUG"] = os.getenv("debug", "False").lower() in ("true", "1", "t")
app.json.sort_keys = False # pyright: ignore[reportAttributeAccessIssue]


async def init_app():
    await Init_module(app)
asyncio.run(init_app())


@app.get("/")
async def root():
    return {"Status": "OK"}
