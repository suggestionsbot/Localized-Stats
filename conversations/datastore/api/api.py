import os
from typing import List

import aiohttp

from conversations import Helper, Conversation
from conversations.abc import DataStore


class ApiStore(DataStore):
    def __init__(self):
        self.access_token = None
        self.refresh_token = None

        self.base_url = "http://127.0.0.1:8000/api/"

    async def _set_new_tokens(self) -> None:
        """Get and set a set of tokens using USERNAME / PASSWORD"""
        payload = {
            "username": os.getenv("API_USERNAME"),
            "password": os.getenv("API_PASSWORD"),
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url + "token/", data=payload) as resp:
                data = await resp.json()
                self.access_token = data["access"]
                self.refresh_token = data["refresh"]

    async def _validate_token(self) -> None:
        """Make a request to test the access token works.
        If it does not, use the refresh token and get a new one.
        """
        if self.access_token is None:
            await self._set_new_tokens()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url + "token/validate/", data={"token": self.access_token}
            ) as resp:
                if resp.status == 200:
                    return

        # We need a new access token
        if self.refresh_token is None:
            await self._set_new_tokens()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url + "token/refresh/", data={"refresh": self.refresh_token}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.access_token = data["access"]
                    return

        # We need both tokens again
        await self._set_new_tokens()

    async def _make_post_request(self, url: str, data: dict) -> dict:
        """Makes a POST request and handles the logic if tokens fail"""
        await self._validate_token()

        headers = {"Authorization": f"Token {self.access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as resp:
                data = await resp.json()
                return data

    async def _make_get_request(self, url: str) -> dict:
        """Makes a GET request
        Assumes any query_params are already url encoded
        """
        await self._validate_token()

        headers = {"Authorization": f"Token {self.access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                return data

    async def create_indexes(self) -> None:
        """Do nothing since indexes are defined at a model level in django"""
        pass

    async def save_conversation(self, conversation: Conversation) -> None:

    async def fetch_conversation(self, identifier: int) -> Conversation:

    async def fetch_current_conversation_count(self) -> int:

    async def fetch_helper(self, identifier: int) -> Helper:

    async def store_helper(self, helper: Helper) -> None:

    async def remove_helper(self, identifier: int) -> None:

    async def fetch_all_conversations(self) -> List[Conversation]:

    async def fetch_all_helpers(self) -> List[Helper]:
