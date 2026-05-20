import os
import discord
import requests
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
MODEL_NAME = "smp-sinj"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🔥 Sinj AI est en ligne sous le pseudo : {client.user}", flush=True)
    print("Prêt à cibler ses victimes sur le serveur. 💀", flush=True)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # S'active si le bot est mentionné ou si on écrit "sinj"
    if client.user.mentioned_in(message) or "sinj" in message.content.lower():
        
        # Nettoyage propre de la mention
        prompt_utilisateur = message.content
        if client.user.mentioned_in(message):
            prompt_utilisateur = prompt_utilisateur.replace(f"<@!{client.user.id}>", "").replace(f"<@{client.user.id}>", "")
        prompt_utilisateur = prompt_utilisateur.strip()
        
        if not prompt_utilisateur:
            prompt_utilisateur = "wsh"

        # --- LA FEAT : INJECTION DE L'IDENTITÉ ---
        # On récupère le pseudo de la personne (ex: Menjabin, Alexandre, Raphaël...)
        pseudo_auteur = message.author.display_name
        
        # On formate le prompt pour donner le contexte à Ollama
        prompt_final = f"L'utilisateur {pseudo_auteur} te dit : {prompt_utilisateur}"
        # ----------------------------------------

        async with message.channel.typing():
            try:
                donnees = {
                    "model": MODEL_NAME,
                    "prompt": prompt_final, # <-- On envoie le prompt avec le pseudo !
                    "stream": False
                }
                
                def faire_requete():
                    return requests.post(OLLAMA_URL, json=donnees, timeout=120)
                
                requete = await asyncio.to_thread(faire_requete)
                
                if requete.status_code == 200:
                    reponse_json = requete.json()
                    replique_bot = reponse_json.get("response", "J'ai buggé, saboteur. 💀")
                    await message.reply(replique_bot)
                else:
                    await message.reply("Ollama répond pas, gros saboteur. 😮‍💨")
                    
            except Exception as erreur:
                print(f"Erreur système : {erreur}", flush=True)
                await message.reply("Erreur de connexion avec mon cerveau. 💀")

client.run(DISCORD_TOKEN)
