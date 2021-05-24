import itertools

from conversations.abc import DataStore


class Manager:
    conversation_identifier = itertools.count().__next__

    def __init__(self, datastore: DataStore):
        self.datastore = datastore
        self.current_conversation = None

    @classmethod
    def get_next_conversation_id(cls) -> int:
        return cls.conversation_identifier()
