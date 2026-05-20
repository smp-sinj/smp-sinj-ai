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

CONSIGNE_EXPERT = (
    " MAIS ATTENTION : L'utilisateur t'a demandé une explication technique/de cours. "
    "Pour cette réponse précise, tu as l'autorisation de faire un long pavé ultra-détaillé, "
    "mathématique et rigoureux. Ne limite pas tes mots. Par contre, garde ton ton méprisant "
    "et lâche obligatoirement tes expressions fétiches comme 'dégâts dégâts' ou 'saboteur' au milieu de tes explications."
)

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

        pseudo_auteur = message.author.display_name
        
        # On formate le prompt pour donner le contexte à Ollama
        prompt_final = f"L'utilisateur {pseudo_auteur} te dit : {prompt_utilisateur}"

        # Gestion du mode "expert" si le flag "explique" est détecté dans le message de l'utilisateur
        system_prompt = ""
        if "explique" in prompt_utilisateur.lower():
            system_prompt = CONSIGNE_EXPERT
            print(f"🧠 Sinj passe en mode Expert pour {pseudo_auteur}", flush=True)

        async with message.channel.typing():
            try:
                donnees = {
                    "model": MODEL_NAME,
                    "prompt": prompt_final, # On envoie le prompt avec le pseudo !
                    "stream": False
                }
                
                # Si le flag "explique" est détecté, on injecte la consigne dans les paramètres de l'API
                if system_prompt:
                    donnees["system"] = system_prompt
                
                def faire_requete():
                    return requests.post(OLLAMA_URL, json=donnees, timeout=300)
                
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