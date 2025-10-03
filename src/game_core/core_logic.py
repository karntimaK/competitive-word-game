from collections import Counter
import random

GREEN = 'G'
YELLOW = 'Y'
GREY = 'X'

class WordGame:
    """Class สำหรับจัดการตรรกะหลักของเกมเดาคำศัพท์"""

    def __init__(self, secret_word=None):
        # ให้สามารถ set secret_word โดยตรงได้
        self.secret_word = secret_word or self._random_word()
        self.word_list = []  # placeholder ยังไม่ใช้ dictionary จริง

    def _random_word(self):
        # mock คำลับ 5 ตัว
        sample_words = ["APPLE", "TRAIN", "CRANE", "ERROR", "BANJO"]
        return random.choice(sample_words)

    def check_guess(self, guess: str) -> list[str]:
        """ให้ผลตอบรับเป็นสี (G, Y, X) สำหรับคำที่ทายเทียบกับคำลับ"""
        guess = guess.upper()
        target = self.secret_word.upper()
        result = [GREY] * 5
        target_counts = Counter(target)

        # Green
        for i in range(5):
            if guess[i] == target[i]:
                result[i] = GREEN
                target_counts[guess[i]] -= 1

        # Yellow
        for i in range(5):
            if result[i] == GREY:
                char = guess[i]
                if target_counts.get(char, 0) > 0:
                    result[i] = YELLOW
                    target_counts[char] -= 1
        return result
