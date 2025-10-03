from collections import Counter
from .dictionary import get_word_list
import random

GREEN = 'G'
YELLOW = 'Y'
GREY = 'X'

class WordGame:
    def __init__(self):
        self.word_list = get_word_list()
        self.secret_word = ""

    def start_new_game(self):
        if not self.word_list:
            raise Exception("No words in dictionary")
        self.secret_word = random.choice(self.word_list)
        return self.secret_word

    def validate_guess(self, guess: str) -> bool:
        guess = guess.upper()
        return len(guess) == 5 and guess in self.word_list

    def check_guess(self, guess: str):
        guess = guess.upper()
        target = self.secret_word.upper()
        result = [GREY]*5
        target_counts = Counter(target)

        # Green
        for i in range(5):
            if guess[i] == target[i]:
                result[i] = GREEN
                target_counts[guess[i]] -= 1
        # Yellow
        for i in range(5):
            if result[i] == GREY and target_counts.get(guess[i], 0) > 0:
                result[i] = YELLOW
                target_counts[guess[i]] -= 1
        return result
