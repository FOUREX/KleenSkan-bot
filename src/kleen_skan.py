from json import loads
from typing import BinaryIO

import aiohttp


class KleenSkanClient:
    def __init__(self, tokens: list[str]):
        self._tokens = tokens

        self._current_token_index = 0
        self._base_url = "https://kleenscan.com/api/v1/"
        self._headers = {"X-Auth-Token": self._tokens[self._current_token_index]}

    async def _make_get_request(self, url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(self._base_url + url, headers=self._headers) as response:
                return loads(await response.text())
    
    async def _make_post_request(self, url: str, *, file: BinaryIO) -> dict:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("path", file)
            data.add_field("avList", "all")

            async with session.post(self._base_url + url, headers=self._headers, data=data) as response:
                return loads(await response.text())

    async def change_token(self) -> int:
        if self._current_token_index + 1 == len(self._tokens):
            self._current_token_index = 0
        else:
            self._current_token_index += 1

        self._headers["X-Auth-Token"] = self._tokens[self._current_token_index]

        return self._current_token_index

    async def get_avlist(self) -> dict:
        return await self._make_get_request("get/avlist")

    async def scan_file(self, file: BinaryIO) -> dict:
        return await self._make_post_request("file/scan", file=file)

    async def get_result(self, scan_token: str):
        return await self._make_get_request(f"file/result/{scan_token}")
