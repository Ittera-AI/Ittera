from pydantic import BaseModel


class RepurposedItem(BaseModel):
    platform: str
    content: str
    format: str


class RepurposeInput(BaseModel):
    original_content: str
    source_platform: str
    target_platforms: list[str]


class RepurposeOutput(BaseModel):
    repurposed: list[RepurposedItem]
