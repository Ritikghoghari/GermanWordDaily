import json
import random
import os
import requests
import time

TARGET_COUNT = 2000
DATA_FILE = 'german_data.json'
URLS = [
    "https://raw.githubusercontent.com/hathibelagal/German-English-JSON-Dictionary/master/german_english.json"
]

def load_local_data(filepath):
    if not os.path.exists(filepath):
        return {"verbs": [], "words": [], "phrases": [], "idioms": []}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_local_data(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_external_dictionary():
    for url in URLS:
        print(f"Trying to download from: {url}")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print("Download successful!")
                return response.json()
            else:
                print(f"Failed with status code: {response.status_code}")
        except Exception as e:
            print(f"Error downloading: {e}")
    return None

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, DATA_FILE)
    
    # 1. Load Local Data
    data = load_local_data(file_path)
    existing_words = set()
    
    for category in data:
        for item in data[category]:
            # Check different keys depending on category structure
            if 'word' in item:
                existing_words.add(item['word'].lower())
            elif 'german' in item:
                existing_words.add(item['german'].lower())

    print(f"Current database has {len(existing_words)} unique entries.")

    # 2. Fetch External Data
    external_dict = fetch_external_dictionary()
    if not external_dict:
        print("Could not download dictionary. Aborting.")
        return

    # External dict is likely {"German": "English", ...} or list.
    # The source 'hathibelagal' is usually a simple list or dict.
    # Let's inspect structure implicitly by trying to iterate.
    
    candidates = []
    if isinstance(external_dict, list):
        # If it's a list of objects
        print("Detected list format.")
        candidates = external_dict
    elif isinstance(external_dict, dict):
        # If it's a simple key-value dict
        print("Detected dict format.")
        for k, v in external_dict.items():
            candidates.append({"word": k, "meaning": v})

    print(f"Found {len(candidates)} total words in external dictionary.")

    # 3. Filter New Words
    new_items = []
    
    # Shuffle first to get random selection
    random.shuffle(candidates)
    
    for item in candidates:
        # Normalize item structure
        word = ""
        meaning = ""
        
        if isinstance(item, dict):
            # Check widely used keys
            word = item.get('word') or item.get('German') or item.get('key')
            meaning = item.get('meaning') or item.get('English') or item.get('value')
            
            # If we still don't have it, maybe it was constructed above as {"word": k, "meaning": v}
        
        if not word:
            continue
            
        if word.lower() not in existing_words:
            # Add to list
            new_entry = {
                "word": word,
                "meaning": meaning,
                "sentence": "Common vocabulary." # Generic sentence
            }
            new_items.append(new_entry)
            
            if len(new_items) >= TARGET_COUNT:
                break
    
    print(f"Selected {len(new_items)} new unique words.")

    # 4. Append and Save
    if 'words' not in data:
        data['words'] = []
        
    data['words'].extend(new_items)
    save_local_data(file_path, data)
    print(f"Successfully saved to {DATA_FILE}. Total words in 'words' category: {len(data['words'])}")

if __name__ == "__main__":
    main()
