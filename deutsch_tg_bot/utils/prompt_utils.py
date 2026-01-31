import os
import re


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


def load_prompt_template_from_file(prompts_dir: str, file_name: str) -> str:
    """Load a prompt template from a file.

    Args:
        prompts_dir: Directory containing prompt files
        file_name: Name of the prompt file
    """
    template_path = os.path.join(prompts_dir, file_name)
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
