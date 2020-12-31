from typing import Callable
from fastapi import Depends

from . import CRUDGenerator, NOT_FOUND

try:
    from databases.core import Database
except ImportError:
    databases_installed = False
else:
    databases_installed = True


class DatabasesCRUDRouter(CRUDGenerator):

    def __init__(self, database, table, *args, **kwargs):
        assert databases_installed, "Databases must be installed to use the DatabasesCRUDRouter."
        self.db = database
        self.table = table
        self._pk = table.primary_key.columns.values()[0].name
        self._pk_col = self.table.c[self._pk]

        super().__init__(*args, **kwargs)

    def _get_all(self) -> Callable:
        async def route():
            q = self.table.select()
            return await self.db.fetch_all(q)

        return route

    def _get_one(self) -> Callable:
        async def route(item_id):
            q = self.table.select().where(self._pk_col == item_id)
            model = await self.db.fetch_one(q)

            if model:
                return model
            else:
                raise NOT_FOUND

        return route

    def _create(self) -> Callable:
        async def route(schema: self.create_schema):
            q = self.table.insert()
            rid = await self.db.execute(query=q, values=schema.dict())
            return {**schema.dict(), self._pk: rid}

        return route

    def _update(self) -> Callable:
        async def route(item_id: int, schema: self.model_cls):
            q = self.table.update().where(self._pk_col == item_id)
            rid = await self.db.execute(query=q, values=schema.dict(exclude={self._pk}))

            if rid:
                return {**schema.dict(), self._pk: rid}
            else:
                raise NOT_FOUND

        return route

    def _delete_all(self) -> Callable:
        async def route():
            q = self.table.delete()
            await self.db.execute(query=q)

            return await self._get_all()()

        return route

    def _delete_one(self) -> Callable:
        async def route(item_id: int):
            q = self.table.delete().where(self._pk_col == item_id)

            row = await self._get_one()(item_id)
            rid = await self.db.execute(query=q)

            if rid:
                return row
            else:
                raise NOT_FOUND

        return route
