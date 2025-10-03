## **README.md — Issue #1 (Full Version)**


# Competitive Web-based Word Guessing Game

## Project Overview
This is a real-time, web-based word guessing game where players compete against each other to find a hidden word. Players receive color-coded feedback for their guesses and can see their opponent's progress in real-time. The goal of this project is to prototype a matchmaking system and basic multiplayer functionality.

---

## Project Structure

```
competitive-word-game/
├── src/
│   ├── server/
│   │   └── app.py
│   └── game_core/
│       ├── core_logic.py
│       ├── dictionary.py
│       └── words.txt
├── tests/
│   ├── test_logic.py
│   └── test_api.py
├── client/
│   └── index.html
├── static/
│   └── main.js
├── requirements.txt
└── README.md
```

---

## Setup Instructions

1. **Clone Repository**
```bash
git clone https://github.com/karntimaK/competitive-word-game.git
cd competitive-word-game
````

2. **Create Virtual Environment**

```bash
python -m venv env
source env/bin/activate   # Linux/Mac
env\Scripts\activate      # Windows
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Run the Server**

```bash
python src/server/app.py
```
