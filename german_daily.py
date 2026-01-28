import json
import random
import os
import requests
import argparse
import google.generativeai as genai
import time

def load_json(filepath):
    """Loads JSON data from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {filepath}")
        return None

def send_discord_notification(webhook_url, content):
    """Sends a message to Discord via Webhook."""
    data = {
        "content": content
    }
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        print("Discord notification sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Discord notification: {e}")

# --- AI GENERATION LOGIC ---
def generate_content_with_ai(count, mode, api_key):
    """Generates content using Gemini API."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = ""
        if mode == "lesson":
            prompt = f"""
            Generate {count} items for a German lesson.
            The list MUST include:
            1. ONE Grammar Rule (with a short explanation and example).
            2. The rest: Unique, intermediate-level Vocabulary (Verbs, Nouns, Idioms).
            
            Return ONLY a raw JSON list of objects. No markdown.
            Structure:
            [
              {{ "category": "grammar", "topic": "Dative Prepositions", "explanation": "Aus, bei, mit, nach...", "example": "Ich gehe mit dem Hund.", "video_search_term": "German grammar Dative Prepositions" }},
              {{ "category": "verb", "word": "laufen", "meaning": "to run", "v1": "laufen", "v2": "lief", "v3": "ist gelaufen", "sentence": "Er läuft schnell." }},
              {{ "category": "word", "word": "der Baum", "meaning": "the tree", "sentence": "Der Baum ist grün." }}
            ]
            """
        elif mode == "quiz":
            # Quiz prompt remains the same
            prompt = f"""
            Generate 1 unique German quiz question.
            Return ONLY a raw JSON object. No markdown formatting.
            Structure:
            {{ "question": "German word/phrase", "answer": "English meaning" }}
            """

        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"AI Generation Failed: {e}")
        return None

# --- LOCAL FALLBACK LOGIC ---
def pick_random_item(data):
    """Picks a random item from the entire pool of items (weighted by size)."""
    # Create a list of (category, item) tuples for every item in the database
    all_items = []
    for category, items_list in data.items():
        for item in items_list:
            all_items.append((category, item))
            
    if not all_items:
        return None, None
        
    return random.choice(all_items)

def format_item_content(item):
    """Formats the item content based on its structure."""
    # Check keys to determine type (flexible for both AI and Local)
    
    # Query parameter encoding helper
    def encode_query(query):
        return requests.utils.quote(query)

    # Grammar
    if 'topic' in item and 'explanation' in item:
        video_link = ""
        if 'video_search_term' in item:
            safe_query = encode_query(item.get('video_search_term'))
            url = f"https://www.youtube.com/results?search_query={safe_query}"
            video_link = f"\n**📺 Watch Video** - [Click Here]({url})"
            
        return (
            f"**📘 Grammar Rule** - {item.get('topic')}\n"
            f"**Explanation** - {item.get('explanation')}\n"
            f"**Example** - {item.get('example')}"
            f"{video_link}"
        )
    # Verb
    elif 'v1' in item and 'v2' in item:
        return (
            f"**Verb** - {item.get('word')}\n"
            f"**Meaning** - {item.get('meaning')}\n"
            f"**Forms** - {item.get('v1')} / {item.get('v2')} / {item.get('v3')}\n"
            f"**Sentence** - {item.get('sentence')}"
        )
    # Noun/Word
    elif 'word' in item and 'sentence' in item:
        return (
            f"**Word** - {item.get('word')}\n"
            f"**Meaning** - {item.get('meaning')}\n"
            f"**Sentence** - {item.get('sentence')}"
        )
    # Phrase/Idiom
    elif 'german' in item:
        return (
            f"**Phrase/Idiom** - {item.get('german')}\n"
            f"**Meaning** - {item.get('english')}\n"
            f"**Context/Literal** - {item.get('context') or item.get('literal', '')}"
        )
    # Generic Fallback
    elif 'word' in item and 'meaning' in item:
         return (
            f"**Word** - {item.get('word')}\n"
            f"**Meaning** - {item.get('meaning')}\n"
            f"**Sentence** - {item.get('sentence', '')}"
        )
         
    return "Error: Unknown item format."

def format_quiz_message(item):
    """Formats the quiz message."""
    # Supports both AI structure and Local structure
    question = item.get('question') or item.get('word') or item.get('german')
    answer = item.get('answer') or item.get('meaning') or item.get('english')
    
    return (
        f"\n**🧠 Daily Quiz**\n"
        f"What is the meaning of: **{question}**?\n"
        f"||{answer}||"
    )

def main():
    parser = argparse.ArgumentParser(description="German Daily Notification")
    parser.add_argument("--mode", choices=['lesson', 'quiz', 'both'], default='both', help="Mode of operation")
    parser.add_argument("--count", type=int, default=1, help="Number of items to send (Lesson mode only)")
    parser.add_argument("--ai_only", action='store_true', help="Force AI only, fail if no key")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Credentials
    # Priority: Environment Variables (GitHub Actions) > config.json (Local)
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if not webhook_url:
        config_path = os.path.join(base_dir, 'config.json')
        config = load_json(config_path)
        if config:
            webhook_url = config.get('webhook_url')
    
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL not found (Set env var or config.json).")
        return

    # 2. Data Source Strategy
    use_ai = bool(gemini_key)
    
    # Always load local data as backup
    data_path = os.path.join(base_dir, 'german_data.json')
    local_data = load_json(data_path)
    
    if use_ai:
        print("Gemini API Key found. Using AI Generation.")
    else:
        print("No Gemini API Key found. Using Local Data.")
        if not local_data:
             print("Error: Local data not found.")
             return

    # --- Mode: Lesson ---
    if args.mode in ['lesson', 'both']:
        messages = []
        ai_success = False
        
        if use_ai:
            print("Requesting AI content...")
            items = generate_content_with_ai(args.count, "lesson", gemini_key)
            if items:
                ai_success = True
                # Ensure it's a list
                if isinstance(items, dict): items = [items]
                for item in items:
                    messages.append(format_item_content(item))
            else:
                print("AI failed (returned None). Switching to local backup...")
                
        # Fallback to local if AI failed or wasn't used
        if (not use_ai or not ai_success) and local_data:
            print("Using Local Data for Lesson...")
            for _ in range(args.count):
                selection = pick_random_item(local_data) # returns (category, item)
                if selection:
                    cat, item = selection
                    messages.append(format_item_content(item))

        # Send Batch
        if messages:
            print(f"Sending {len(messages)} lesson items...")
            current_chunk = "**🇩🇪 German Daily Lesson**"
            for msg in messages:
                separator = "\n\n"
                to_add = separator + msg
                if len(current_chunk) + len(to_add) > 1900:
                    send_discord_notification(webhook_url, current_chunk)
                    current_chunk = "**🇩🇪 Continued...**" + to_add
                else:
                    current_chunk += to_add
            if current_chunk:
                send_discord_notification(webhook_url, current_chunk)

    # --- Mode: Quiz ---
    if args.mode in ['quiz', 'both']:
        msg_quiz = None
        ai_success = False
        
        if use_ai:
             item = generate_content_with_ai(1, "quiz", gemini_key)
             if item:
                 ai_success = True
                 # AI returns simple object {question, answer}
                 msg_quiz = format_quiz_message(item)
             else:
                 print("AI Quiz failed. Switching to local backup...")
        
        if (not use_ai or not ai_success) and local_data:
            print("Using Local Data for Quiz...")
            selection = pick_random_item(local_data)
            if selection:
                cat, item = selection
                msg_quiz = format_quiz_message(item)

        if msg_quiz:
            print("Sending Quiz...")
            send_discord_notification(webhook_url, msg_quiz)

if __name__ == "__main__":
    main()
