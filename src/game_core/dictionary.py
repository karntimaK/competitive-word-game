import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_FILE = os.path.join(BASE_DIR, "words.txt")

def get_word_list():
    if not os.path.exists(DICT_FILE):
        raise Exception(f"Dictionary file not found: {DICT_FILE}")

    with open(DICT_FILE, "r", encoding="utf-8") as f:
        words = [line.strip().upper() for line in f if line.strip()]
    return words
