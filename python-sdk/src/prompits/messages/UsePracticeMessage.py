# UsePracticeMessage is a message that requests the use of a practice
# contains the practice name, and the sender and recipients, and arguments

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..AgentAddress import AgentAddress
from ..Message import Message, Attachment

class UsePracticeRequest(Message):
    """
    A message that requests the use of a practice.
    """
    def __init__(self, practice_name: str, sender: AgentAddress, recipients: List[AgentAddress], arguments: Dict[str, Any] = None, msg_id: str = None, attachments: List[Attachment] = None):
        """
        Initialize a UsePracticeRequest message.
        
        Args:
            practice_name (str): The name of the practice to use
            sender (AgentAddress): The sender of the message
            recipients (List[AgentAddress]): The recipients of the message
            arguments (Dict[str, Any]): The arguments to pass to the practice
            msg_id (str): The message ID
            attachments (List[Attachment]): The attachments to pass to the practice
        """
        super().__init__(
            type="UsePracticeRequest",
            body={"practice_name": practice_name, "arguments": arguments or {}},
            sender=sender,
            recipients=recipients,
            msg_id=msg_id,
            attachments=attachments
        )
        self.practice_name = practice_name
        self.arguments = arguments or {}

    @property
    def args(self) -> Dict[str, Any]:
        return self.arguments

    @staticmethod
    def FromJson(json_data: Dict[str, Any]) -> 'UsePracticeRequest':
        msg = Message.FromJson(json_data)
        return UsePracticeRequest(
            practice_name=msg.body["practice_name"],
            arguments=msg.body["arguments"],
            sender=msg.sender,
            recipients=msg.recipients,
            msg_id=msg.msg_id,
            attachments=msg.attachments
        )

    def __str__(self):
        return f"UsePracticeMessage(practice_name={self.body['practice_name']}, sender={self.sender}, recipients={self.recipients}, arguments={self.body['arguments']})"

    def __repr__(self):
        return self.__str__()
    
    def ToJson(self) -> dict:
        json_msg = super().ToJson()
        json_msg['body']['practice_name'] = self.body['practice_name']
        json_msg['body']['arguments'] = self.body['arguments']
        return json_msg

    def FromJson(self, json_data: Dict[str, Any]):
        super().FromJson(json_data)
        self.body['practice_name'] = json_data['body']['practice_name']
        self.body['arguments'] = json_data['body']['arguments']
    
class UsePracticeResponse(Message):
    """
    A message that responds to a UsePracticeRequest.
    """
    def __init__(self, practice_name: str, result: Any, sender: AgentAddress, recipients: List[AgentAddress], error: Optional[str] = None, msg_id: Optional[str] = None, attachments: Optional[List[Attachment]] = None):
        """
        Initialize a UsePracticeResponse message.
        
        Args:
            practice_name (str): The name of the practice to use
            result (Any): The result of the practice
            sender (AgentAddress): The sender of the message
            recipients (List[AgentAddress]): The recipients of the message
            error (Optional[str]): The error of the practice
            msg_id (Optional[str]): The message ID
            attachments (Optional[List[Attachment]]): The attachments of the message
        """
        super().__init__(
            type="UsePracticeResponse",
            body={"practice_name": practice_name, "result": result, "error": error},
            sender=sender,
            recipients=recipients,
            msg_id=msg_id,
            attachments=attachments
        )
        self.practice_name = practice_name
        self.result = result
        self.error = error

    @staticmethod
    def FromJson(json_data: Dict[str, Any]) -> 'UsePracticeResponse':
        msg = Message.FromJson(json_data)
        return UsePracticeResponse(
            practice_name=msg.body["practice_name"],
            result=msg.body["result"],
            error=msg.body.get("error"),
            sender=msg.sender,
            recipients=msg.recipients,
            msg_id=msg.msg_id,
            attachments=msg.attachments
        )

    def ToJson(self):
        """
        Convert the UsePracticeResponse message to a JSON dictionary.
        
        Returns:
            dict: A dictionary containing the message information
        """
        # if sender and recipients are AgentAddress objects, convert them to json   
        if isinstance(self.sender, AgentAddress):
            sender = self.sender.ToJson()
        else:
            sender = self.sender
            
        # Initialize recipients variable
        recipients = []
        if hasattr(self, 'recipients') and self.recipients is not None:
            if isinstance(self.recipients, list) and all(isinstance(recipient, AgentAddress) for recipient in self.recipients):
                recipients = [recipient.ToJson() for recipient in self.recipients]
            else:
                recipients = self.recipients
                
        return {
            "type": self.type,
            "body": self.body,
            "sender": sender,
            "recipients": recipients,
            "msg_id": self.msg_id,
            "attachments": self.attachments
        }
    
    def FromJson(self, json_data):
        self.body = json.loads(json_data)
        self.sender = AgentAddress(self.body['sender'])
        self.recipients = [AgentAddress(recipient) for recipient in self.body['recipients']]
        self.msg_id = self.body['msg_id']
        self.attachments = [Attachment(attachment['name'], attachment['content']) for attachment in self.body['attachments']]