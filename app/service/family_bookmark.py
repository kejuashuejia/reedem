import os
import json
from typing import List, Dict

class FamilyBookmark:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.bookmarks: List[Dict] = []
            self.filepath = "family_bookmark.json"

            if os.path.exists(self.filepath):
                self.load_bookmarks()
            else:
                self._save([])  # create empty file

            self._initialized = True

    def _save(self, data: List[Dict]):
        """Helper to write JSON safely."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_bookmarks(self):
        """Load bookmarks from JSON file."""
        with open(self.filepath, "r", encoding="utf-8") as f:
            self.bookmarks = json.load(f)

    def save_bookmarks(self):
        """Save current bookmarks to JSON file."""
        self._save(self.bookmarks)

    def add_bookmark(self, name: str, family_code: str, order: int) -> bool:
        """Add a family bookmark if it does not already exist."""
        key = (family_code, order)

        if any(
            (b["family_code"], b["order"]) == key
            for b in self.bookmarks
        ):
            print("Bookmark already exists.")
            return False

        self.bookmarks.append(
            {
                "name": name,
                "family_code": family_code,
                "order": order,
            }
        )
        self.save_bookmarks()
        print("Bookmark added.")
        return True

    def remove_bookmark(self, family_code: str, order: int) -> bool:
        """Remove a family bookmark if it exists. Returns True if removed."""
        for i, b in enumerate(self.bookmarks):
            if (
                b["family_code"] == family_code
                and b["order"] == order
            ):
                del self.bookmarks[i]
                self.save_bookmarks()
                print("Bookmark removed.")
                return True
        print("Bookmark not found.")
        return False

    def get_bookmarks(self) -> List[Dict]:
        """Return all bookmarks."""
        return self.bookmarks.copy()

FamilyBookmarkInstance = FamilyBookmark()
