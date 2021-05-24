from motor.motor_asyncio import AsyncIOMotorClient

from .document import Document
from ...abc import DataStore


class Mongo(DataStore):
    def __init__(self, connection_string):
        self.db = AsyncIOMotorClient(connection_string).stats

        self.conversations = Document(self.db, "conversations")
        self.helpers = Document(self.db, "helpers")
