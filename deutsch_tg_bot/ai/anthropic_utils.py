import os
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


def load_prompt_template_from_file(file_name: str) -> str:
    template_path = os.path.join(os.path.dirname(__file__), "prompts", file_name)
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
