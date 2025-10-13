import app.menus.banner as banner
ascii_art = banner.load("https://me.mashu.lol/mebanner880.png", globals())

from html.parser import HTMLParser
import os
import re
import textwrap
import sys

def log_progress(process_number, process_name, percentage, success=None):
    """
    Displays a progress bar with status in a simplified format.

    Args:
        process_number (int): The sequential number of the process.
        process_name (str): The name of the process.
        percentage (int): The completion percentage (0-100).
        success (bool, optional): True for success (✓), False for failure (X), None for in-progress.
    """
    hashes = '#' * (percentage // 10)

    status_symbol = ""
    if success is True:
        status_symbol = " ✓"
    elif success is False:
        status_symbol = " X"

    # Pad with spaces to overwrite previous, longer lines
    output_line = f"{process_number}. {process_name} {hashes}{status_symbol}"

    # Use \r to stay on the same line for updates
    sys.stdout.write(f"\r{output_line.ljust(80)}")
    sys.stdout.flush()

    if success is not None:
        sys.stdout.write('\n')
        sys.stdout.flush()

def clear_screen():
    print("Clearing screen...")
    os.system('cls' if os.name == 'nt' else 'clear')
    if ascii_art:
        ascii_art.to_terminal(columns=55)

def pause():
    input("\nPress enter to continue...")

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