# Message is a class for information interchange between agents
# MEssage is an abstract class
# Message contains type, sent_time, body, attachments, sender, recipients


from datetime import datetime
from typing import Dict, Any, List, Optional
from .AgentAddress import AgentAddress

class Attachment:
    def __init__(self, name: str, content_type: str, data: Any):
        self.name = name
        self.content_type = content_type
        self.data = data

    def ToJson(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "content_type": self.content_type,
            "data": self.data
        }

    @staticmethod
    def FromJson(json_data: Dict[str, Any]) -> 'Attachment':
        return Attachment(
            name=json_data["name"],
            content_type=json_data["content_type"],
            data=json_data["data"]
        )

class Message:
    def __init__(self, type: str, body: Dict[str, Any], sender: AgentAddress, recipients: List[AgentAddress], msg_id: Optional[str] = None, attachments: Optional[List[Attachment]] = None, timestamp: Optional[datetime] = None):
        self.type = type
        self.body = body
        self.sender = sender
        self.recipients = recipients
        self.msg_id = msg_id
        self.attachments = attachments or []
        self.timestamp = timestamp or datetime.now()

    def ToJson(self) -> Dict[str, Any]:
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
        return f"Message(type={self.type}, sent_time={self.timestamp}, body={self.body}, attachments={self.attachments})"
    
    def __repr__(self):
        return self.__str__()
