import json
import os
import logging

class PortfolioDatabase:
    def __init__(self, data_dir: str = "data"):
        # Resolve path relative to the caller (app root)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(base_dir, data_dir)
        self.profile_path = os.path.join(self.data_dir, "user_profile.json")
        self.history_path = os.path.join(self.data_dir, "recommendation_history.json")
        
        os.makedirs(self.data_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        if not os.path.exists(self.profile_path):
            with open(self.profile_path, "w") as f:
                json.dump({}, f)
                
        if not os.path.exists(self.history_path):
            with open(self.history_path, "w") as f:
                json.dump([], f)

    def load_profile(self) -> dict:
        try:
            with open(self.profile_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading profile: {e}")
            return {}

    def save_profile(self, profile: dict):
        try:
            with open(self.profile_path, "w") as f:
                json.dump(profile, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving profile: {e}")

    def add_recommendation(self, recommendation: dict):
        try:
            history = self.get_history()
            history.append(recommendation)
            with open(self.history_path, "w") as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            logging.error(f"Error adding recommendation: {e}")

    def get_history(self) -> list:
        try:
            with open(self.history_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error getting history: {e}")
            return []

    def clear_all(self):
        try:
            with open(self.profile_path, "w") as f:
                json.dump({}, f)
            with open(self.history_path, "w") as f:
                json.dump([], f)
        except Exception as e:
            logging.error(f"Error clearing database: {e}")
