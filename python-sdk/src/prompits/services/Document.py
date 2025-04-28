class Document:
    def __init__(self, name: str, properties: dict, document_id: str=None):
        self.document_name = name
        self.document_properties = properties
        self.document_id = document_id

    def set_document_id(self, document_id: str):
        self.document_id = document_id

    def FromJson(self, json_data):
        self.document_name = json_data["document_name"]
        self.document_properties = json_data["document_properties"]
        if "document_id" in json_data:
            self.document_id = json_data["document_id"]
        else:
            self.document_id = None

    def ToJson(self):
        json_data = {   
            "document_name": self.document_name,
            "document_properties": self.document_properties
        }
        if self.document_id is not None:
            json_data["document_id"] = self.document_id
        return json_data
    
    def __str__(self):
        return f"Document(document_name={self.document_name}, document_properties={self.document_properties})"