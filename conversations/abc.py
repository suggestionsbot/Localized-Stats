from typing import Protocol, List

from conversations import Conversation, Helper


class DataStore(Protocol):
    __slots__ = ()

    async def save_conversation(self, conversation: Conversation) -> None:
        """
        Given a :class: Conversation object, save
        it to the datastore such that is can be
        retrieved and rebuilt at a later date

        Parameters
        ----------
        conversation : Conversation
            The conversation to save
        """
        raise NotImplementedError

    async def fetch_conversation(self, identifier: int) -> Conversation:
        """
        Given an identifier for a :class: Conversation
        build and return a valid Conversation object

        Parameters
        ----------
        identifier : int
            The conversation to build

        Returns
        -------
        Conversation
            A valid :class: Conversation class

        """
        raise NotImplementedError

    async def fetch_current_conversation_count(self) -> int:
        """
        Fetch the current conversation id so we can
        set our manager class correctly

        Returns
        -------
        int
            The current conversation count
        """
        raise NotImplementedError

    async def fetch_helpers(self) -> List[Helper]:
        """
        Get all of the currently stored helpers

        Returns
        -------
        List[Helper]
            A list of all valid helper objects
        """
        raise NotImplementedError

    async def fetch_helper(self, identifier: int) -> Helper:
        """
        Given an identifier, return a valid
        :class: Helper object based on the
        given data

        Parameters
        ----------
        identifier : int
            The id of the helper to fetch

        Returns
        -------
        Helper
            The valid helper object
        """
        raise NotImplementedError

    async def store_helper(self, helper: Helper) -> None:
        """
        Store a helper object persistently

        Parameters
        ----------
        helper : Helper
            The helper to store
        """
        raise NotImplementedError

    async def remove_helper(self, identifier: int) -> None:
        """
        Given an id, remove the given
        helper from persistent storage

        Parameters
        ----------
        identifier : int
            The helper to remove
        """
        raise NotImplementedError

    async def get_all_conversations(self) -> List[dict]:
        """
        Returns a list of all possible conversations yea idk

        Returns
        -------
        List[dict]
            A list of conversations used to
            build dataclasses
        """
        raise NotImplementedError

    async def get_all_helpers(self) -> List[dict]:
        """
        Returns a list of all helpers to make dataclasses for

        Returns
        -------
        List[dict]
            A list of helpers
        """
        raise NotImplementedError
