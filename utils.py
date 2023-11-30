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

import xml.etree.ElementTree as ET
import json

def xml_to_dict(xml_str):
    try:
        root = ET.fromstring(xml_str)
        return {root.tag: xml_to_dict_recur(root)}
    except Exception as e:
        print(e)

def xml_to_dict_recur(element):
    if len(element) == 0:
        return element.text
    else:
        result = {}
        for child in element:
            child_dict = xml_to_dict_recur(child)
            if child.tag in result:
                if isinstance(result[child.tag], list):
                    result[child.tag].append(child_dict)
                else:
                    result[child.tag] = [result[child.tag], child_dict]
            else:
                result[child.tag] = child_dict
        return result

import difflib

def json_similarity(json1, json2):
    # Convert JSON objects to strings
    str1 = json.dumps(json1, sort_keys=True)
    str2 = json.dumps(json2, sort_keys=True)
    
    # Create a SequenceMatcher object to compare the strings
    s = difflib.SequenceMatcher(None, str1, str2)
   
    # Get the similarity ratio between the two strings
    similarity_score = s.ratio()
    
    return similarity_score

