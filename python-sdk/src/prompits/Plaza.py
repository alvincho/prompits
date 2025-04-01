# Plaza is a service provide agents to store and retrieve data
# it is a Pit and abstract class
# it has predefiineed schema for the data that can be stored
# it has StoreAd, RetrieveAd, UpdateAd, SearchAd, DeleteAd practices

from datetime import datetime
import json
from typing import Dict, Any, List, Optional
from .Schema import TableSchema
from .Practice import Practice
from .LogEvent import LogEvent
from .Pool import Pool
from .pools.DatabasePool import DatabasePool
from .Pit import Pit

class Ad:
    def __init__(self, id: str, data: dict):
        self.id = id
        self.data = data

class Plaza(Pit):
    def __init__(self, name: str, description: str, table_schema: TableSchema, pool: DatabasePool):
        super().__init__(name, description or f"Plaza {name}")
        self.set_schema(table_schema)
        self.pool = pool

    def ToJson(self):
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.schema.ToJson(),
            "pool": self.pool.ToJson()
        }
    
    def FromJson(self, json: dict):
        self.name = json["name"]
        self.description = json["description"]
        self.schema = TableSchema.FromJson(json["schema"])
        self.pool = DatabasePool.FromJson(json["pool"])
    def set_schema(self, schema: dict):
        self.schema = schema

    # Store an ad in the plaza's pool
    def StoreAd(self, table_name: str, ad: Ad):
        self.pool.Store(ad.id, ad.data)

    def RetrieveAd(self, table_name: str, id: str):
        return self.pool.Retrieve(id)

    def UpdateAd(self, table_name: str, id: str, data: dict):
        self.pool.Update(table_name, id, data)

    def SearchAd(self, table_name: str, where: dict):
        return self.pool.Search(table_name, where)

    def DeleteAd(self, id: str):
        self.pool.Delete(id)

    def Store(self, key: str, data: Dict[str, Any]) -> bool:
        raise NotImplementedError("Store method not implemented")

    def Retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Retrieve method not implemented")

    def Search(self, where: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError("Search method not implemented")

    def Update(self, key: str, data: Dict[str, Any]) -> bool:
        raise NotImplementedError("Update method not implemented")

    def Delete(self, key: str) -> bool:
        raise NotImplementedError("Delete method not implemented")

    def ToJson(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "Plaza",
            "pool": self.pool.ToJson() if self.pool else None,
            "schema": self.schema.ToJson() if self.schema else None
        }
