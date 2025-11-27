import re
from typing import TypedDict


class MessageDict(TypedDict):
    role: str
    content: str


def replace_promt_placeholder(prompt: str) -> str:
    """
    Unitility function to replace {{placeholder}} with %(placeholder)s,
    so prompts can be copy-pasted from Claude Console.
    """
    return re.sub(r"\{\{(\w+)\}\}", r"%(\1)s", prompt)


def extract_tag_content(completion: str, tag: str) -> str | None:
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    start_index = completion.find(start_tag)
    end_index = completion.find(end_tag)
    if start_index != -1 and end_index != -1:
        return completion[start_index + len(start_tag) : end_index].strip()
    return None
