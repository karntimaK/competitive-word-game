## **README.md**

---

Colab : [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]

<p align="center">
  <video src="https://files.catbox.moe/bcst24.mp4" controls width="700">
    Your browser does not support the video tag.
  </video>
</p>


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
│   ├── styles.css
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
```
3. **Activate Virtual Environment**
```bash
source env/bin/activate   # Linux/Mac
```
```bash
env\Scripts\activate      # Windows
```

4. **Install Dependencies**

```bash
pip install -r requirements.txt
```

5. **Run the Server**

```bash
python src/server/app.py
```
