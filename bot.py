import os
import discord
import requests
import json
from dotenv import load_dotenv
# Configuration
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Mets ton token généré ici
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
MODEL_NAME = "smp-sinj"

intents = discord.Intents.default()
intents.message_content = True  # Obligatoire pour lire les messages
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🔥 Sinj AI est en ligne sous le pseudo : {client.user}")
    print("Prêt à distribuer des dégâts sur le serveur. 💀")

@client.event
async def on_message(message):
    # Sécurité : le bot ne doit pas se répondre à lui-même
    if message.author == client.user:
        return

    # Le bot s'active si on l'évoque par son nom 'sinj' ou s'il est directement mentionné
    if client.user.mentioned_in(message) or "sinj" in message.content.lower():
        
        # On nettoie le texte pour enlever la mention brute (ex: <@123456789>)
        prompt_utilisateur = message.content.replace(f"<@!{client.user.id}>", "").replace(f"<@{client.user.id}>", "").strip()
        
        # Si le message contient juste la mention et rien d'autre, on simule un salut
        if not prompt_utilisateur:
            prompt_utilisateur = "wsh"

        # On affiche l'indicateur "Sinj est en train d'écrire..." sur Discord
        async with message.channel.typing():
            try:
                # Données envoyées à l'API locale d'Ollama
                donnees = {
                    "model": MODEL_NAME,
                    "prompt": prompt_utilisateur,
                    "stream": False  # Desactive le streaming pour envoyer le bloc complet d'un coup
                }
                
                # Envoi de la requête au Ollama qui tourne sur le Pi 5
                requete = requests.post(OLLAMA_URL, json=donnees, timeout=10)
                
                if requete.status_code == 200:
                    reponse_json = requete.json()
                    replique_bot = reponse_json.get("response", "J'ai buggé, saboteur. 💀")
                    
                    # On répond directement sous le message de la personne
                    await message.reply(replique_bot)
                else:
                    await message.reply("Ollama répond pas, gros saboteur. 😮‍💨")
                    
            except Exception as erreur:
                print(f"Erreur système : {erreur}")
                await message.reply("Erreur de connexion avec mon cerveau. 💀")

client.run(DISCORD_TOKEN)
