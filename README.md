# Ethiopian Telegram Dating Bot

A Telegram-based dating bot bridging diaspora and home connections.

## Local Setup

1. Copy `.env.example` to `.env` and fill in your `BOT_TOKEN`.
2. Start the database and Redis using Docker Compose:
   ```bash
   docker compose up -d
   ```
3. Install dependencies (recommend using a virtual environment):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```bash
   alembic upgrade head
   ```
5. Run the bot:
   ```bash
   python -m src.bot.main
   ```
