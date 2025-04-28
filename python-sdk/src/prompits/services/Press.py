# Press is a service that allows you to create and manage documents or knowledge bases
# Press can do full text search, vector search, graph search, and more

import datetime
from enum import Enum
from prompits.services.Service import Service
from prompits.Pool import Pool
from prompits.Schema import TableSchema, DataType
from prompits.pools.DatabasePool import DatabasePool, SearchType
from prompits.Practice import Practice
from prompits.services.Document import Document
from prompits.services.Publication import Publication
from prompits.services.Ollama import Ollama

class Press(Service):
    """Class representing a Press service for managing press operations."""
    
    def __init__(self, name: str, description: str, 
                 pool: DatabasePool, vector_pool: DatabasePool=None, 
                 graph_pool: DatabasePool=None,
                 table_prefix: str="press_",
                 embedding_models: dict={}):
        """Initialize the Press service with a name and pressure.
        
        Args:
            name (str): The name of the press.
            description (str): The description of the press.
            pool (Pool): The pool associated with the press.
        """
        super().__init__(name, description)
        self.vector_pool = vector_pool
        self.graph_pool = graph_pool
        self.embedding_models = embedding_models
        self.pool = pool
        self.table_prefix = table_prefix
        # use ollama for now
        self.ollama = Ollama("Ollama")

        self.AddPractice(Practice(name="EmbedText", function=self._EmbedText, description="Embed text using the embedding model"))
        self.AddPractice(Practice(name="CreatePublication", function=self._CreatePublication, description="Create a publication"))
        self.AddPractice(Practice(name="GetPublication", function=self._GetPublication, description="Get a publication"))
        self.AddPractice(Practice(name="UpdatePublication", function=self._UpdatePublication, description="Update a publication"))
        self.AddPractice(Practice(name="DeletePublication", function=self._DeletePublication, description="Delete a publication"))
        self.AddPractice(Practice(name="SearchPublications", function=self._SearchPublications, description="Search for publications"))
        self.AddPractice(Practice(name="CreateDocument", function=self._CreateDocument, description="Create a document"))
        self.AddPractice(Practice(name="GetDocument", function=self._GetDocument, description="Get a document"))
        self.AddPractice(Practice(name="UpdateDocument", function=self._UpdateDocument, description="Update a document"))
        self.AddPractice(Practice(name="DeleteDocument", function=self._DeleteDocument, description="Delete a document"))
        self.AddPractice(Practice(name="SearchDocuments", function=self._SearchDocuments, description="Search for documents"))
        self.AddPractice(Practice(name="UpdateEntity", function=self._UpdateEntity, description="Update an entity"))
        # initialize the pools
        self.initialize_pools()

    def _get_document_table_schema(self, partition_name: str):
        return TableSchema({
            "name":self.table_prefix + partition_name + "_document",
            "description": "Press document table",
            "primary_key": ["document_id"],
            "rowSchema": {
                "document_id": DataType.UUID,
                "document_name": DataType.STRING,
                "document_properties": DataType.JSON,
                "owner": DataType.UUID
            }
        })
        
    def initialize_pools(self):
        # create tables
        # document is the basic element of information in the press
        # entity data table keeps track of all entities in the press

        # create system partition
        self._create_partition("prompits")
        self._create_partition("general")

        model_defs=self.UsePractice("SearchDocuments",
                    {"document_name": "llm_models"}, partition_list=["prompits"])
        print(f"Found llm_models in {self.pool.name}: {model_defs}")
        if len(model_defs["prompits"])>0:
            self.llm_models=model_defs["prompits"][0]
        else:
            doc = Document("llm_models", {"document_name":"llm_models","document_properties":{}})
            self.UsePractice("CreateDocument", doc, "prompits")
            model_defs=self.UsePractice("SearchDocuments", 
                    {"document_name": "llm_models"}, partition_list=["prompits"])
            print(f"Found llm_models in {self.pool.name}: {model_defs}")    
            if len(model_defs["prompits"])>0:
                self.llm_models=model_defs["prompits"][0]
            else:
                raise ValueError("Failed to create llm_models")


        self.entity_table_schema = TableSchema({
            "name": self.table_prefix + "entity",
            "description": "Press entity table",
            "primary_key": ["entity_id"],
            "rowSchema": {
                "entity_id": DataType.UUID,
                "entity_name": DataType.STRING,
                "entity_type": DataType.STRING,
                "entity_properties": DataType.JSON,
                "last_updated": DataType.DATETIME,
                "last_seen": DataType.DATETIME
            }
        })
        if not self.pool.UsePractice("TableExists", self.entity_table_schema.name):
            self.pool.UsePractice("CreateTable", self.entity_table_schema.name, self.entity_table_schema)

        # create embedding tables
        self._create_embedding_tables("general")
        self._create_embedding_tables("prompits")

        
    def _get_text_table_schema(self, partition_name: str):
        return TableSchema({
            "name": self.table_prefix + partition_name + "_text",
            "description": "Press text content table",
            "primary_key": ["text_id"],
            "rowSchema": {
                "text_id": DataType.UUID,
                "text": DataType.STRING
            }
        })

    def _get_text_origin_table_schema(self, partition_name: str):
        return TableSchema({
            "name": self.table_prefix + partition_name + "_text_origin",
            "description": "Origins of each Press text (agent, practice, pathway, etc.)",
            "primary_key": ["text_id", "origin_type", "origin_id"],
            "rowSchema": {
                "text_id": DataType.UUID,
                "origin_type": DataType.STRING,
                "origin_id": DataType.STRING,
                "origin_field": DataType.STRING,
                "origin_properties": DataType.JSON
            }
        })      

    def _create_partition(self, partition_name: str):

        document_table_schema = self._get_document_table_schema(partition_name)
        if not self.pool.UsePractice("TableExists", document_table_schema.name):
            self.pool.UsePractice("CreateTable", document_table_schema.name, document_table_schema)

        # text is slice of text from a document
        # text can be a paragraph, a sentence, a word, or a character
        text_table_schema = self._get_text_table_schema(partition_name)
        if not self.pool.UsePractice("TableExists", text_table_schema.name):
            self.pool.UsePractice("CreateTable", text_table_schema.name, text_table_schema)

        # text_origin_table_schema keeps track of the origins of each text
        # same text can have multiple origins
        text_origin_table_schema = self._get_text_origin_table_schema(partition_name)
        if not self.pool.UsePractice("TableExists", text_origin_table_schema.name):
            self.pool.UsePractice("CreateTable", text_origin_table_schema.name, text_origin_table_schema)
        # raise not implemented error if graph_pool is not None
        if self.graph_pool is not None:
            self.log("Graph search is not implemented", "WARNING")

    def _create_embedding_tables(self, partition_name: str):
        # create embeddings if vector_pool is not None
        if self.vector_pool is not None:
            # search embeddings in document table
            # if not found, create embeddings
            for model in self.embedding_models:
                # search embeddings in text table
                if model not in self.llm_models["document_properties"]["models"]:
                    self.llm_models["document_properties"]["models"][model]=model
                # create embeddings
                # each embedding model has a table in the vector_pool because different dimensions are used for different models
                embedding_schema=TableSchema({
                    "name": self.table_prefix + partition_name + "_" + model + "_embedding",
                    "description": "Embedding model table",
                    "primary_key": ["text_id"],
                    "rowSchema": {
                        "text_id": DataType.UUID,
                        "embedding": {"type":DataType.VECTOR, "dimension":model.dimension}
                    }
                })
                if not self.vector_pool.UsePractice("TableExists", embedding_schema.name):
                    self.vector_pool.UsePractice("CreateTable", embedding_schema.name, embedding_schema.rowSchema)
        # update llm_models in document table
        document_table_name=self.table_prefix + partition_name + "_document"

        self.UsePractice("UpdateDocument",{"document_id":self.llm_models["document_id"],
                                            "document_properties": self.llm_models["document_properties"]},partition_name)

    def _EmbedText(self, text: str, embedding_model: str):
        # embed text using the embedding model
        # return the embedding
        # for now use local ollama

        return self.pool.UsePractice("EmbedText", {"text":text, "embedding_model":embedding_model})

    def _UpdateEntity(self, entity: dict):
        raise NotImplementedError("Not implemented")

    def _CreatePublication(self, publication: Publication):
        raise NotImplementedError("Not implemented")

    def _GetPublication(self, publication_id: str):
        raise NotImplementedError("Not implemented")

    def _UpdatePublication(self, publication: Publication):
        raise NotImplementedError("Not implemented")

    def _DeletePublication(self, publication_id: str):
        raise NotImplementedError("Not implemented")

    def _SearchPublications(self, query: str, search_type: SearchType=SearchType.FULL_TEXT):
        raise NotImplementedError("Not implemented")

    def _CreateDocument(self, document: Document, partition_name: str="general"):
        table_name=self.table_prefix + partition_name + "_document"
        self.pool.UsePractice("Insert", table_name,document.ToJson(), self._get_document_table_schema(partition_name))

    def _GetDocument(self, document_id: str, partition_name: str="general"):
        return self.UsePractice("Select", {"document_id":document_id, "partition_name":partition_name})

    def _UpdateDocument(self, document: Document, partition_name: str="general"):
        if isinstance(document, dict):
            doc_json=document
        else:
            doc_json=document.ToJson()
        self.pool.UsePractice("Update", self.table_prefix + partition_name + "_document", doc_json, {"document_id":  doc_json["document_id"]}, self._get_document_table_schema(partition_name))

    def _DeleteDocument(self, document_id: str, partition_name: str="general"):
        self.pool.UsePractice("Delete", self.table_prefix + partition_name + "_document", {"document_id":document_id}, self._get_document_table_schema(partition_name))

    def _SearchDocuments(self, query: dict, search_type: SearchType=SearchType.FULL_TEXT,
                         top_k: int=10, top_p: float=1.0, partition_list: list[str]=["general"],
                         **kwargs):
        # Use Practice Search of the pool
        results={}
        if search_type==SearchType.FULL_TEXT:
            for partition in partition_list:
                results[partition]=self.pool.UsePractice("Search",self.table_prefix + partition + "_document",query,  top_k=top_k, top_p=top_p)
        elif search_type==SearchType.VECTOR:
            for partition in partition_list:
                for model in self.embedding_models:
                    embedding_table=self.table_prefix + partition + "_" + model + "_embedding"
                    embedding=self.pool.UsePractice("VectorSearch", {"query":query, "embedding_table":embedding_table, "top_k":top_k, "top_p":top_p, "partition_list":[partition]})
                results[partition]=self.pool.UsePractice("VectorSearch", {"query":query, "embedding":embedding, "embedding_table":embedding_table, "top_k":top_k, "top_p":top_p, "partition_list":[partition]})
        elif search_type==SearchType.GRAPH:
            raise NotImplementedError("Graph search is not implemented")
        return results
