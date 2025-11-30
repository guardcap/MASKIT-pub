from typing import List, Dict, Any
from collections import defaultdict
from typing import Tuple

class meta:
    def __init__(
        self,
        sender: dict={"team","role"},
        recipient: dict={"domain","role"},
        purpose: str="",
        channel: str="",
        timestamp: str="",
        audience:str="",
        jurisdiction: str=""
    ):
        self.sender = sender
        self.recipient = recipient
        self.purpose = purpose
        self.channel = channel
        self.timestamp = timestamp
        self.audience = audience
        self.jurisdiction = jurisdiction
        
    def __repr__(self):
        return (
            f"Entity(entity='{self.entity}', score={self.score:.2f}, "
            f"word='{self.word}', start={self.start}, end={self.end}, "
            f"pageIndex={self.pageIndex}, bbox={self.bbox})"
        )