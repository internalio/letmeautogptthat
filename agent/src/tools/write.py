from typing import Type

from pydantic import BaseModel, Field

from langchain.tools.base import BaseTool


class WriteInput(BaseModel):
    """Input for WriteTool."""

    text: str = Field(..., description="text to write")


class WriteTool(BaseTool):
    buffer: str = ""
    name: str = "write_text"
    args_schema: Type[BaseModel] = WriteInput
    description: str = "Write text"

    def _run(self, text: str) -> str:
        self.buffer += text

    async def _arun(self, tool_input: str) -> str:
        # TODO: Add aiofiles method
        raise NotImplementedError
