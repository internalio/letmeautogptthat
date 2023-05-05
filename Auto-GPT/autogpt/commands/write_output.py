"""File operations for AutoGPT"""
from __future__ import annotations

from autogpt.commands.command import command


@command("write_output", "Write output", '"output": "<output>"')
def read_file(output: str) -> str:
    """Read a file and return the contents

    Args:
        output (str): The output to write

    Returns:
        output
    """
    return output
