import os
import json

class FamilyBookmark:
    _instance_ = None
    _initialized_ = False
    
    bookmarks = []
    # Format: [{"family_code": str, "family_name": str}]
    
    FILE_PATH = "family_bookmark.json"

    def __new__(cls, *args, **kwargs):
        if not cls._instance_:
            cls._instance_ = super().__new__(cls)
        return cls._instance_

    def __init__(self):
        if not self._initialized_:
            if os.path.exists(self.FILE_PATH):
                self.load_bookmarks()
            else:
                self.write_bookmarks() # Create empty file
            self._initialized_ = True

    def load_bookmarks(self):
        with open(self.FILE_PATH, "r") as f:
            self.bookmarks = json.load(f)

    def write_bookmarks(self):
        with open(self.FILE_PATH, "w") as f:
            json.dump(self.bookmarks, f, indent=4)

    def add_bookmark(self, family_code: str, family_name: str):
        # Avoid duplicates
        if not any(b['family_code'] == family_code for b in self.bookmarks):
            self.bookmarks.append({"family_code": family_code, "family_name": family_name})
            self.write_bookmarks()
            print("Bookmark berhasil ditambahkan.")
        else:
            print("Bookmark untuk family code ini sudah ada.")

    def remove_bookmark(self, family_code: str):
        self.bookmarks = [b for b in self.bookmarks if b['family_code'] != family_code]
        self.write_bookmarks()
        print("Bookmark berhasil dihapus.")

    def get_bookmarks(self):
        return self.bookmarks

FamilyBookmarkInstance = FamilyBookmark()
