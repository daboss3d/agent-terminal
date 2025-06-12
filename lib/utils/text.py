import re
import os
from typing import List


class Colors:
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m" 

def clear_markdown_to_color(text: str) -> str:
    """
    This function takes a markdown formatted text as input, processes it to add color to code blocks,
    and then returns the modified text.

    Args:
        text (str): The input string which may contain Markdown notation for code blocks.

    Returns:
        str: Colored text where code blocks are highlighted.
    """
    lines = text.split('\n')
    new_lines = []
    in_code_block = False

    for line in lines:
        if '```' in line:
            in_code_block = not in_code_block
            # new_lines.append( "") # line.strip() )
        elif in_code_block:
            new_lines.append(Colors.CYAN + line.strip() + Colors.ENDC)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def clear_markdown(text: str) -> str:

    fs = text.splitlines()
    # Remove markdown code blocks
    response = "\n".join([s for s in fs if "```" not in s])

    # Remove backticks
    response = "\n".join(
        [e for e in response.split("`") if e.strip() != ""])

    response = response.strip()

    return response



def ask_yes_no(question) -> bool :
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in ['y', 'n']:
            if answer == 'y':
                return True
            return False

        else:
            print("Please respond with 'y' or 'n'.")



def remove_string_from_list_in_place(string_to_remove : str, list_of_strings : list):
    """
    Removes "string_to_remove" from each string in a list, modifying the list in-place.
    Handles potential extra whitespace after removal.

    Args:
        list_of_strings (list): A list of strings.
    """
    for i in range(len(list_of_strings)):
        if "--stream" in list_of_strings[i]:
            list_of_strings[i] = list_of_strings[i].replace("--stream", "").strip()
         
def remove_string_from_list_new(string_to_remove : str, list_of_strings : list):
    """
    Removes "string_to_remove" from each string in a list and returns a new list.
    Handles potential extra whitespace after removal.

    Args:
        list_of_strings (list): A list of strings.

    Returns:
        list: A new list with "string_to_remove" removed from relevant strings.
    """
    modified_list = []
    for s in list_of_strings:
        if string_to_remove in s:
            modified_list.append(s.replace(string_to_remove, "").strip())
        else:
            modified_list.append(s)
    return modified_list       





# def extract_quoted_text(text):
#     # Match everything between matching " and ", or ' and ', using regex
#     # matches = re.findall(r"(?<!\\)[\'\"].*?(?<!\\)[\'\"]", text)
#     # return matches
#     # If input is not iterable, convert it into an array
#     if isinstance(text, str):
#         text = [text]

#     quoted_lists = []
#     for t in text:
#         matches = re.findall(r"(?<!\\)[\'\"].*?(?<!\\)[\'\"]", t)
#         quoted_lists.extend(matches)

#     return quoted_lists


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

def extract_quoted_text_inside_quoted(strings_list: list[str]) -> list[str]:
    """
    Extracts text enclosed within the outermost double ("") or single ('') quotes
    from each string in a given list.

    If a string starts and ends with matching quotes, the entire content
    between those quotes is extracted. If quotes appear internally within
    a larger string, the content between the *first* detected opening quote
    and its *last* matching closing quote is extracted.

    Args:
        strings_list: A list of strings to process.

    Returns:
        A list of strings containing the extracted quoted text.
        Returns an empty string for any input string that does not
        contain valid quoted text according to the rules.
    """
    extracted_texts = []

    for s in strings_list:
        extracted = ""  # Default to an empty string if no valid extraction is found

        # Find the index of the first occurrence of double quotes
        first_double_quote_idx = s.find('"')
        # Find the index of the first occurrence of single quotes
        first_single_quote_idx = s.find("'")

        start_idx = -1  # Initialize start index for the extracted text
        start_quote_char = None  # To store the type of the first encountered quote

        # Determine which type of quote appears first in the string
        if first_double_quote_idx != -1 and \
           (first_single_quote_idx == -1 or first_double_quote_idx < first_single_quote_idx):
            # A double quote was found first, or it was the only type of quote found
            start_quote_char = '"'
            start_idx = first_double_quote_idx
        elif first_single_quote_idx != -1:
            # A single quote was found first (and double quotes either weren't found
            # or appeared after the single quote)
            start_quote_char = "'"
            start_idx = first_single_quote_idx
        # If both first_double_quote_idx and first_single_quote_idx are -1,
        # it means no quotes were found in the string. In this case, start_idx
        # remains -1, and the default empty string will be appended.

        if start_idx != -1:
            # If a starting quote was found, find the last occurrence of the *same*
            # type of quote character. This handles cases where the quoted text
            # contains nested quotes of a *different* type or even the same type,
            # as long as they don't form the *outermost* boundary for the *first*
            # detected quote.
            end_idx = s.rfind(start_quote_char)

            # Check if a valid closing quote was found *after* the starting quote
            if end_idx > start_idx:
                # Extract the substring between the start and end quotes (exclusive of quotes)
                extracted = s[start_idx + 1:end_idx]

        extracted_texts.append(extracted)

    return extracted_texts

# def extract_quoted_text(strings_list: list[str]) -> list[str]:
#     """
#     Extracts text that contains double ("") or single ('') quotes
#     from each string in a given list.

#     If a string contains any double or single quotes, the entire original
#     string is returned. Otherwise, an empty string is returned.

#     Args:
#         strings_list: A list of strings to process.

#     Returns:
#         A list of strings. For each input string that contains quotes,
#         the original string is returned. For strings without quotes,
#         an empty string is returned.
#     """
#     extracted_texts = []

#     for s in strings_list:
#         # Check if the string contains any double quotes
#         if '"' in s:
#             extracted_texts.append(s)
#         # Check if the string contains any single quotes
#         elif "'" in s:
#             extracted_texts.append(s)
#         else:
#             # No quotes found, so return an empty string
#             extracted_texts.append("")

#     return extracted_texts

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


def hello_text():
    print("hello from text")