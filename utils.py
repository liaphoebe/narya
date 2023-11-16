import os
import tiktoken

def count_tokens_with_tiktoken(text: str, model: str = 'gpt-3.5-turbo') -> int:
    """
    Count the number of tokens in a text string using OpenAI's Tiktoken.
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
    

def create_key_from_path(path):
    """Create a dictionary key from a path name."""
    # Normalize the path and remove the .py 
    normalized_path = os.path.normpath(path)
    path_without_extension, _ = os.path.splitext(normalized_path)
    
    if not path_without_extension.startswith("/"):
        path_without_extension = "_" + path_without_extension

    return path_without_extension.replace(os.sep, "_")

def get_value(dictionary, string):
    # split the string into list and reverse it
    string_list = string.split('/')[::-1]
    
    for key in dictionary.keys():
        # split the keys, reverse them and check if any part of string is in the key
        if any(x in key.split('/')[::-1] for x in string_list):
            return dictionary.get(key)

    # in case no match is found
    return None

