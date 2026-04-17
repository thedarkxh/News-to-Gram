import os
import json
from instagrapi import Client

ig_client = Client()

def login_instagram():
    session_data = os.getenv("IG_SESSION") # Get the JSON string from Secrets
    
    if session_data:
        try:
            print("Attempting to login via session...")
            session_dict = json.loads(session_data)
            ig_client.set_settings(session_dict)
            ig_client.login(os.getenv("IG_USERNAME"), os.getenv("IG_PASSWORD"))
            print("Session login successful!")
            return True
        except Exception as e:
            print(f"Session expired or invalid: {e}")
    
    # Fallback to normal login if session fails
    try:
        print("Falling back to password login...")
        ig_client.login(os.getenv("IG_USERNAME"), os.getenv("IG_PASSWORD"))
        return True
    except Exception as e:
        print(f"Total Login Failure: {e}")
        return False
