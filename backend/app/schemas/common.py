from pydantic import BaseModel


class Page(BaseModel):
    total: int
    page: int
    page_size: int


class Message(BaseModel):
    detail: str
