import re
from typing import List

COLORS = {
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "blue": "\033[94m",
    "reset": "\033[0m"
}

def colorize(text: str, color_name: str) -> str:
    """
    Applies ANSI color codes to the given text.

    Args:
        text (str): The text to colorize.
        color_name (str): The name of the color (e.g., "green", "red").

    Returns:
        str: The colorized text if color_name is valid, otherwise the original text.
    """
    color_code = COLORS.get(color_name.lower())
    if color_code:
        return f"{color_code}{text}{COLORS['reset']}"
    return text

def extract_quoted_text(strings: List[str]) -> List[str]:
    """
    Extracts text inside double ("") or single ('') quotes from a list of strings.

    Args:
        strings (List[str]): A list of input strings.

    Returns:
        List[str]: A list of all quoted substrings found.
    """
    quoted_texts = []
    pattern = r'["\'](.*?)["\']'  # Non-greedy match between quotes

    for s in strings:
        matches = re.findall(pattern, s)
        quoted_texts.extend(matches)

    return quoted_texts

def remove_empty_or_whitespace_strings(strings_list: list[str]) -> list[str]:
    """
    Removes strings that are empty or contain only whitespace characters
    from a given list of strings.

    Args:
        strings_list: A list of strings to filter.

    Returns:
        A new list containing only strings that are not empty and
        contain at least one non-whitespace character.
    """
    filtered_strings = [s for s in strings_list if s.strip()]
    return filtered_strings