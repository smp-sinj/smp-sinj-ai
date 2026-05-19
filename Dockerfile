FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances
RUN pip install --no-cache-dir discord.py requests python-dotenv

# Copie du code
COPY bot.py .

# Commande de lancement
CMD ["python", "bot.py"]
