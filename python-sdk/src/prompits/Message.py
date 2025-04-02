# Message is a class for information interchange between agents
# MEssage is an abstract class
# Message contains type, sent_time, body, attachments, sender, recipients


from datetime import datetime
from typing import Dict, Any, List, Optional
from .AgentAddress import AgentAddress

class Attachment:
    """
    Represents a file or data attachment that can be included with a message.
    
    Attachments can contain various types of data like documents, images, or
    any serializable content that needs to be transmitted along with a message.
    """
    
    def __init__(self, name: str, content_type: str, data: Any):
        """
        Initialize an Attachment instance.
        
        Args:
            name: Name or identifier for the attachment
            content_type: MIME type or format identifier for the content
            data: The actual attachment data
        """
        self.name = name
        self.content_type = content_type
        self.data = data

    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the attachment to a JSON-serializable dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the attachment
        """
        return {
            "name": self.name,
            "content_type": self.content_type,
            "data": self.data
        }

    @staticmethod
    def FromJson(json_data: Dict[str, Any]) -> 'Attachment':
        """
        Create an Attachment from JSON data.
        
        Args:
            json_data: Dictionary containing serialized attachment data
            
        Returns:
            Attachment: New instance initialized with the data
        """
        return Attachment(
            name=json_data["name"],
            content_type=json_data["content_type"],
            data=json_data["data"]
        )

class Message:
    """
    Represents a communication between agents in the system.
    
    Message is the core communication unit that contains information sent between
    agents including the message type, content body, sender, recipients, and
    optional attachments.
    """
    
    def __init__(self, type: str, body: Dict[str, Any], sender: AgentAddress, recipients: List[AgentAddress], msg_id: Optional[str] = None, attachments: Optional[List[Attachment]] = None, timestamp: Optional[datetime] = None):
        """
        Initialize a Message instance.
        
        Args:
            type: Type identifier for the message
            body: Dictionary containing the message content
            sender: Address of the agent sending the message
            recipients: List of agent addresses to receive the message
            msg_id: Optional unique message identifier
            attachments: Optional list of attachments to include
            timestamp: Optional timestamp for the message (defaults to current time)
        """
        self.type = type
        self.body = body
        self.sender = sender
        self.recipients = recipients
        self.msg_id = msg_id
        self.attachments = attachments or []
        self.timestamp = timestamp or datetime.now()

    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the message to a JSON-serializable dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the message
        """
        sender_json = str(self.sender)
        return {
            "type": self.type,
            "body": self.body,
            "sender": sender_json,
            "recipients": [str(r) for r in self.recipients],
            "msg_id": self.msg_id,
            "attachments": [a.ToJson() for a in self.attachments],
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def FromJson(json_data: Dict[str, Any]) -> 'Message':
        """
        Create a Message from JSON data.
        
        Args:
            json_data: Dictionary containing serialized message data
            
        Returns:
            Message: New instance initialized with the data
        """
        return Message(
            type=json_data["type"],
            body=json_data["body"],
            sender=AgentAddress.FromJson(json_data["sender"]),
            recipients=[AgentAddress.FromJson(r) for r in json_data["recipients"]],
            msg_id=json_data.get("msg_id"),
            attachments=[Attachment.FromJson(a) for a in json_data.get("attachments", [])],
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )

    # declare variables
    type: str
    msg_id: str
    timestamp: datetime
    body: dict
    attachments: list
    sender: AgentAddress
    recipients: list[AgentAddress]

    def __str__(self):
        """
        Get a string representation of the message.
        
        Returns:
            str: String representation
        """
        return f"Message(type={self.type}, sent_time={self.timestamp}, body={self.body}, attachments={self.attachments})"
    
    def __repr__(self):
        """
        Get a string representation for debugging.
        
        Returns:
            str: String representation
        """
        return self.__str__()
