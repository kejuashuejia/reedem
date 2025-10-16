import app.menus.banner as banner
from html.parser import HTMLParser
import os
import re
import textwrap
import json
import urllib.request
import urllib.error

WIDTH = 55

class Style:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    width = WIDTH
    print("=" * width)
    print(f" Special Thx for Baka Mitai 😘".center(width))
    print("=" * width)
    print("")
    # Load notification from remote JSON; show only if present
    notif_url = "https://pastebin.com/raw/2UfYSacE"
    notifications = load_notifications(notif_url)
    for notif in notifications:
        text = notif.get('text')
        color = notif.get('color')
        if text:
            wrapped_text = textwrap.wrap(text, width=width)
            if color:
                style_code = getattr(Style, color.upper(), "")
                reset_code = Style.RESET if style_code else ""
                for line in wrapped_text:
                    print(f"{style_code}{line.center(width)}{reset_code}")
            else:
                for line in wrapped_text:
                    print(line.center(width))
    print("")

def print_header(title):
    clear_screen()
    print(title.center(WIDTH))
    print("=" * WIDTH)
        

def pause():
    input("\nPress enter to continue...")

def format_quota(byte_val: int) -> str:
    if byte_val is None:
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while byte_val >= power and n < len(power_labels):
        byte_val /= power
        n += 1
    return f"{byte_val:.2f} {power_labels[n]}"

class HTMLToText(HTMLParser):
    def __init__(self, width=80):
        super().__init__()
        self.width = width
        self.result = []
        self.in_li = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.in_li = True
        elif tag == "br":
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "li":
            self.in_li = False
            self.result.append("\n")

    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.in_li:
                self.result.append(f"- {text}")
            else:
                self.result.append(text)

    def get_text(self):
        # Join and clean multiple newlines
        text = "".join(self.result)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        # Wrap lines nicely
        return "\n".join(textwrap.wrap(text, width=self.width, replace_whitespace=False))

def display_html(html_text, width=80):
    parser = HTMLToText(width=width)
    parser.feed(html_text)
    return parser.get_text()

def wrap_text(text, width=WIDTH):
    """Wraps text to the given width, preserving existing newlines."""
    lines = text.split('\n')
    wrapped_lines = []
    for line in lines:
        wrapped_lines.extend(textwrap.wrap(line, width=width))
    return '\n'.join(wrapped_lines)

def load_notifications(url):
    """Fetch notification JSON from url and return a list of dicts.
    It can handle a single notification object, a list of notification objects,
    or multiple notification objects as separate keys in the JSON.
    """
    def _find_notif_objects(data):
        if not isinstance(data, dict):
            return []

        # Check for a primary 'notifikasi' key which could be a list or a dict
        primary_notif = data.get('notifikasi')
        if primary_notif:
            if isinstance(primary_notif, list):
                return primary_notif  # It's a list of notifs
            if isinstance(primary_notif, dict):
                return [primary_notif] # It's a single notif

        # If no primary 'notifikasi' key, look for 'notifik...', etc.
        notifs = []
        for key, value in sorted(data.items()): # sort to get notif1, notif2 in order
            if key.lower().startswith('notifik') and isinstance(value, dict):
                notifs.append(value)
        
        return notifs

    def _extract_text_and_color(obj):
        if not isinstance(obj, dict):
            return None, None
        # 1) text can be a string
        text_field = obj.get('text')
        if isinstance(text_field, str):
            return text_field, obj.get('color')
        # 2) text can be a dict of language variants
        if isinstance(text_field, dict):
            # prefer 'prassa'
            lang_text = text_field.get('prassa')
            if isinstance(lang_text, str):
                return lang_text, obj.get('color')
            # fallback to any first available string
            for v in text_field.values():
                if isinstance(v, str):
                    return v, obj.get('color')
        # 3) direct 'prassa' key (string or nested dict)
        pr = obj.get('prassa')
        if isinstance(pr, str):
            return pr, obj.get('color')
        if isinstance(pr, dict):
            # prassa may itself contain text and color
            if isinstance(pr.get('text'), str):
                return pr.get('text'), pr.get('color') or obj.get('color')
        return None, obj.get('color')

    notifications = []
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            if getattr(resp, "status", 200) != 200:
                return []
            body = resp.read().decode('utf-8')
            data = json.loads(body)
            
            notif_objects = _find_notif_objects(data)

            for obj in notif_objects:
                text, color = _extract_text_and_color(obj)
                if text:
                    notifications.append({'text': text, 'color': color})
            return notifications
    except Exception:
        return []
