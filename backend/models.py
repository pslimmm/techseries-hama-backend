from pydantic import BaseModel
from typing import List

class ChatbotInit(BaseModel):
    lang: str
    newSessionId: str
    oldSessionId: str

class ChatbotMessage(BaseModel):
    last_message: str
    message: str
    lang: str
    sessionId: str

class IngestedText(BaseModel):
    chunks: List[str]
    doc: str
    translate: bool

