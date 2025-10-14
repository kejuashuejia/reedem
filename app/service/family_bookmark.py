import os
import json

class FamilyBookmark:
    _instance_ = None
    _initialized_ = False
    
    bookmarks = []
    # Format: [{"name": str, "family_code": str, "order": int}]
    
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
            try:
                bookmarks_data = json.load(f)
                migrated_bookmarks = []
                needs_migration = False
                for bm in bookmarks_data:
                    if 'name' not in bm:
                        needs_migration = True
                        if 'package_name' in bm and 'order' in bm:
                            migrated_bookmarks.append({
                                "name": bm.get("package_name", "N/A"),
                                "family_code": bm["family_code"],
                                "order": bm["order"]
                            })
                        # Ignore old bookmarks with 'family_name' as they are not compatible
                    else:
                        migrated_bookmarks.append(bm)
                
                if needs_migration:
                    self.bookmarks = migrated_bookmarks
                    self.write_bookmarks()
                    print("Bookmark file has been migrated to a new format. Some old bookmarks might have been removed.")
                else:
                    self.bookmarks = bookmarks_data

            except json.JSONDecodeError:
                self.bookmarks = [] # Reset if file is corrupted or empty

    def write_bookmarks(self):
        with open(self.FILE_PATH, "w") as f:
            json.dump(self.bookmarks, f, indent=4)

    def add_bookmark(self, name: str, family_code: str, order: int):
        # Avoid duplicates
        if not any(b['family_code'] == family_code and b['order'] == order for b in self.bookmarks):
            self.bookmarks.append({"name": name, "family_code": family_code, "order": order})
            self.write_bookmarks()
            print("Bookmark berhasil ditambahkan.")
        else:
            print("Bookmark untuk family code dan order ini sudah ada.")

    def remove_bookmark(self, index: int):
        if 0 <= index < len(self.bookmarks):
            del self.bookmarks[index]
            self.write_bookmarks()
            print("Bookmark berhasil dihapus.")
        else:
            print("Index bookmark tidak valid.")

    def get_bookmarks(self):
        return self.bookmarks

FamilyBookmarkInstance = FamilyBookmark()
