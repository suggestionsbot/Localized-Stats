import datetime
import os
from typing import List, Tuple

import aiohttp
from attr import asdict

from conversations import Helper, Conversation, Message
from conversations.abc import DataStore


class ApiStore(DataStore):
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.last_validated = None

        self.session = aiohttp.ClientSession()

        # self.base_url = "https://stats.koldfusion.xyz/api/"
        self.base_url = "http://127.0.0.1:8000/api/"

    async def _set_new_tokens(self) -> None:
        """Get and set a set of tokens using USERNAME / PASSWORD"""
        payload = {
            "username": os.getenv("API_USERNAME"),
            "password": os.getenv("API_PASSWORD"),
        }
        async with self.session.post(self.base_url + "token/", data=payload) as resp:
            data = await resp.json()
            self.access_token = data["access"]
            self.refresh_token = data["refresh"]

    async def _validate_token(self) -> None:
        """Make a request to test the access token works.
        If it does not, use the refresh token and get a new one.
        """
        if self.last_validated is not None:
            # Check if validated recently
            diff = datetime.datetime.now() - self.last_validated
            if diff.total_seconds() < 3600:  # validate token's once an hour
                return

        print("Actually validating token")
        self.last_validated = datetime.datetime.now()

        if self.access_token is None:
            await self._set_new_tokens()

        async with self.session.post(
            self.base_url + "token/validate/", data={"token": self.access_token}
        ) as resp:
            if resp.status == 200:
                return

        # We need a new access token
        if self.refresh_token is None:
            await self._set_new_tokens()

        async with self.session.post(
            self.base_url + "token/refresh/", data={"refresh": self.refresh_token}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.access_token = data["access"]
                return

        # We need both tokens again
        await self._set_new_tokens()

    async def _make_post_request(self, url: str, data: dict) -> Tuple[int, dict]:
        """Makes a POST request and handles the logic if tokens fail"""
        await self._validate_token()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with self.session.post(url, json=data, headers=headers) as resp:
            data = await resp.json()
            return resp.status, data

    async def _make_get_request(self, url: str) -> Tuple[int, dict]:
        """Makes a GET request
        Assumes any query_params are already url encoded
        """
        await self._validate_token()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with self.session.get(url, headers=headers) as resp:
            data = await resp.json()
            return resp.status, data

    @staticmethod
    def _convert_to_datetime(incoming: str) -> datetime.datetime:
        """Given a string in the format "%f:%S:%M:%H:%d:%m:%Y"
        return the valid datetime object
        """
        return datetime.datetime.strptime(incoming, "%f:%S:%M:%H:%d:%m:%Y")

    @staticmethod
    def _convert_from_datetime(outoging: datetime.datetime) -> str:
        """Given a datetime object return a string in the format %f:%S:%M:%H:%d:%m:%Y"""
        return outoging.strftime("%f:%S:%M:%H:%d:%m:%Y")

    @staticmethod
    def _convert_to_timedelta(incoming: str) -> datetime.timedelta:
        """Given a string denoting a timedelta, create and return one"""
        return datetime.timedelta(seconds=float(incoming))

    async def create_indexes(self) -> None:
        """Do nothing since indexes are defined at a model level in django"""
        pass

    async def save_conversation(self, conversation: Conversation) -> None:
        data = asdict(conversation, recurse=True)

        data["start_time"] = self._convert_from_datetime(data["start_time"])
        data["end_time"] = self._convert_from_datetime(data["end_time"])

        for m in data["messages"]:
            m["timestamp"] = self._convert_from_datetime(m["timestamp"])

        status, _ = await self._make_post_request(
            self.base_url + "conversation/create/", data
        )
        assert status == 201

    async def fetch_conversation(self, identifier: int) -> Conversation:
        status, return_data = await self._make_get_request(
            self.base_url + f"conversation/get/?id={identifier}"
        )
        assert status == 200

        return_data["start_time"] = self._convert_to_datetime(return_data["start_time"])
        return_data["end_time"] = self._convert_to_datetime(return_data["end_time"])

        for m in return_data["messages"]:
            m["timestamp"] = self._convert_to_datetime(m["timestamp"])

        return Conversation(**return_data)

    async def fetch_current_conversation_count(self) -> int:
        status, return_data = await self._make_get_request(
            self.base_url + "conversation/count/"
        )
        assert status == 200

        return return_data["conversation_count"]

    async def fetch_helper(self, identifier: int) -> Helper:
        status, return_data = await self._make_get_request(
            self.base_url + f"helper/get/?discord_id={identifier}"
        )
        assert status == 200

        dates = []
        for date in return_data["conversation_length"]:
            dates.append(self._convert_to_timedelta(date))

        return_data["conversation_length"] = dates

        return Helper(**return_data)

    # noinspection PyMethodOverriding
    async def store_helper(
        self, helper: Helper, username: str, password: str, is_helper: bool = False
    ) -> None:
        """Creates a user for Django and gives em access"""
        data = {
            "username": username,
            "password": password,
            "discord_user_id": helper.identifier,
            "is_helper": is_helper,
        }
        status, _ = await self._make_post_request(
            self.base_url + "account/create/", data
        )
        assert status == 201

    async def fetch_all_users(self):
        """Returns a list of all internal usernames"""
        status, return_data = await self._make_get_request(
            self.base_url + "account/get/all/"
        )
        assert status == 200
        return return_data

    async def remove_helper(self, identifier: int) -> None:
        """Doesnt look used so ok atm"""
        pass  # TODO Impl

    async def fetch_all_conversations(self) -> List[Conversation]:
        status, return_data = await self._make_get_request(
            self.base_url + "conversation/get/all/"
        )
        assert status == 200

        conversations = []
        for conversation in return_data:
            conversation["identifier"] = conversation.pop("id")
            conversation["start_time"] = self._convert_to_datetime(
                conversation["start_time"]
            )
            conversation["end_time"] = self._convert_to_datetime(
                conversation["end_time"]
            )

            messages = []
            for m in conversation["messages"]:
                m.pop("id")
                m.pop("conversation")
                m["timestamp"] = self._convert_to_datetime(m["timestamp"])
                messages.append(Message(**m))

            conversation["messages"] = messages

            conversations.append(Conversation(**conversation))

        return conversations

    async def fetch_all_helpers(self) -> List[Helper]:
        status, return_data = await self._make_get_request(
            self.base_url + "helper/get/all/"
        )
        assert status == 200

        helpers = []
        for helper in return_data:
            dates = []
            for date in helper["conversation_length"]:
                dates.append(self._convert_to_timedelta(date))

            helper["conversation_length"] = dates

            helpers.append(Helper(**helper))

        return helpers
