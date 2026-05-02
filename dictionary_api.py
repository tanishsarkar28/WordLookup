import requests
import logging
import os
import sys
import json

_OFFLINE_DICT = None

def get_offline_dict_path():
    """Returns the correct path to the offline dictionary file."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'dictionary_compact.json')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dictionary_compact.json')

def get_offline_definition(word):
    """Fetches definition from the bundled offline dictionary JSON."""
    global _OFFLINE_DICT
    if _OFFLINE_DICT is None:
        try:
            with open(get_offline_dict_path(), 'r', encoding='utf-8') as f:
                _OFFLINE_DICT = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load offline dictionary: {e}")
            return {"error": "Offline dictionary unavailable.", "word": word}
    
    definition = _OFFLINE_DICT.get(word.lower())
    if definition:
        # In this simple dictionary format, meanings are single strings
        return {
            "word": word,
            "phonetic": "",
            "meaning": definition,
            "example": "",
            "synonyms": []
        }
    return {"error": "No definition found (Offline Mode).", "word": word}

def fetch_definition(word):
    """
    Fetches the definition of a word from the Free Dictionary API.
    Returns a dictionary with parsed data or falls back to offline dict on error.
    """
    word = word.strip().lower()
    if not word:
        return None

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 404:
            logging.info(f"Word not found online: {word}, checking offline dict.")
            return get_offline_definition(word)
            
        response.raise_for_status()
        data = response.json()
        
        if not data or not isinstance(data, list):
            return get_offline_definition(word)
            
        entry = data[0]
        result = {
            "word": entry.get("word", word),
            "phonetic": entry.get("phonetic", ""),
            "meaning": "",
            "example": "",
            "synonyms": []
        }
        
        # Look for the first valid meaning and example
        for meaning in entry.get("meanings", []):
            for definition in meaning.get("definitions", []):
                if not result["meaning"]:
                    result["meaning"] = definition.get("definition", "")
                if not result["example"] and "example" in definition:
                    result["example"] = definition["example"]
                
                # If we have both, we can stop searching definitions
                if result["meaning"] and result["example"]:
                    break
                    
            if "synonyms" in meaning and meaning["synonyms"]:
                result["synonyms"].extend(meaning["synonyms"])
                
        # Limit synonyms
        result["synonyms"] = list(set(result["synonyms"]))[:5]
        
        return result

    except requests.exceptions.RequestException as e:
        logging.warning(f"API Request failed for '{word}', falling back to offline: {e}")
        return get_offline_definition(word)
    except Exception as e:
        logging.error(f"Unexpected error fetching definition for '{word}': {e}")
        return get_offline_definition(word)

