# Publication is a text representation of information or knowledge.
# It can be a text, a table, a chart, a image, a video, etc.
# It can be a document, a pathway, a practice, an agent, a service, an api, etc.
# It is used in the context of a Press.
from enum import Enum
import datetime

class PublicationType(Enum):
    FILE = "file"
    URL = "url"
    PATHWAY = "pathway"
    PRACTICE = "practice"
    AGENT = "agent"
    SERVICE = "service"
    API = "api"


class Publication:
    """Publication is a text representation of a document.
    It can be a text, a table, a chart, a image, a video, etc.
    """
    def __init__(self, name: str, description: str, type: PublicationType, properties: dict={}):
        self.name = name
        self.type = type
        self.description = description
        self.properties = properties
        self.create_time = datetime.now()
        self.update_time = datetime.now()
        self.embedding = {

        }

