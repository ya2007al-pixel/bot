import os

class Config:
    API_ID = int(os.environ.get("API_ID", "33296024"))
    API_HASH = os.environ.get("API_HASH", "2ca6c382c66fa301a67997270836e933")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8498812432:AAGh7AOmkr7zZs-yS8BoqDI7GeZx4DqGOL4")