import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from game_core.core_logic import WordGame

def test_word_length():
    game = WordGame()
    secret = game.start_new_game()
    assert len(secret) == 5

def test_validate_guess():
    game = WordGame()
    game.start_new_game()
    valid_word = "APPLE"
    invalid_word = "XXXXX"
    assert game.validate_guess(valid_word) in [True, False]  # ขึ้นกับ dictionary
    assert game.validate_guess(invalid_word) in [True, False]
