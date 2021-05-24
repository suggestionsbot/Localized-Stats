import collections


class Document:
    def __init__(self, connection, document_name):
        self.db = connection[document_name]

    # <-- Pointer Methods -->
    async def find(self, filter_dict):
        return await self.find_by_custom(filter_dict)

    async def delete(self, filter_dict):
        await self.delete_by_custom(filter_dict)

    async def update(self, filter_dict, update_data, option="set", *args, **kwargs):
        await self.update_by_custom(filter_dict, update_data, option, *args, **kwargs)

    async def upsert(self, filter_dict, update_data, option="set", *args, **kwargs):
        await self.upsert_custom(filter_dict, update_data, option, *args, **kwargs)

    # <-- Actual Methods -->
    async def get_all(self, filter_dict=None, *args, **kwargs):
        if filter_dict is None:
            filter_dict = {}

        return await self.db.find(filter_dict, *args, **kwargs).to_list(None)

    async def find_by_custom(self, filter_dict):
        self.__ensure_dict(filter_dict)

        return await self.db.find_one(filter_dict)

    async def find_many_by_custom(self, filter_dict):
        self.__ensure_dict(filter_dict)

        return await self.db.find(filter_dict).to_list(None)

    async def delete_by_custom(self, filter_dict):
        self.__ensure_dict(filter_dict)

        if await self.find_by_custom(filter_dict) is None:
            return

        return await self.db.delete_many(filter_dict)

    async def insert(self, data):
        self.__ensure_dict(data)

        await self.db.insert_one(data)

    async def upsert_custom(
        self, filter_dict, update_data, option="set", *args, **kwargs
    ):
        await self.update_by_custom(
            filter_dict, update_data, option, upsert=True, *args, **kwargs
        )

    async def update_by_custom(
        self, filter_dict, update_data, option="set", *args, **kwargs
    ):
        self.__ensure_dict(filter_dict)
        self.__ensure_dict(update_data)

        if not bool(await self.find_by_custom(filter_dict)):
            # Insert
            return await self.insert({**filter_dict, **update_data})

        # Update
        await self.db.update_one(
            filter_dict, {f"${option}": update_data}, *args, **kwargs
        )

    async def unset(self, filter_dict, to_delete):
        self.__ensure_dict(to_delete)
        self.__ensure_dict(filter_dict)

        await self.db.update_one(filter_dict, {"$unset": to_delete})

    async def increment(self, filter_dict, field_to_increment, amount):
        await self.db.update_one(filter_dict, {"$inc": {field_to_increment: amount}})

    async def get_document_count(self) -> int:
        return await self.db.count_documents({})

    @staticmethod
    def __ensure_dict(data):
        assert isinstance(data, collections.abc.Mapping)
