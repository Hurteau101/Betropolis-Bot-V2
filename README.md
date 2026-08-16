# Betropolis Bot V2

A Discord bot that scans esports DFS lines across PrizePicks, Underdog, and ParlayPlay, finds the biggest projection mismatches, and automatically posts ready-made slip suggestions to Discord.

## Tech Stack

- **Language:** Python

## Getting Started

### Prerequisites

- Python 3.10+
- Redis
- An API key for the esports odds data source
- A Discord webhook URL

### Installation

```bash
# Clone the repository
git clone https://github.com/Hurteau101/Betropolis-Bot-V2.git
cd Betropolis-Bot-V2

# Create a virtual environment
python -m venv venv

# Activate it
Windows - venv\Scripts\activate | Linux - venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with your API key, Discord webhook URL, and Redis connection details.

### Running the Bot

```bash
python runner.py
```

## How It Works

1. `runner.py` kicks off each book (PrizePicks, Underdog, Underdog Streaks) in a randomized order
2. Each book class fetches the latest esports lines and filters out books with non-standard multipliers
3. Lines are compared against a base book (or the average of two books) to find the biggest mismatches
4. Qualifying differences are grouped into slips of the configured size
5. Each slip is formatted with unit size and expected payout, then sent to Discord
