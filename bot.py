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

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_URL = os.getenv("MISTRAL_URL", "https://api.mistral.ai/v1/chat/completions")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
BACKEND = os.getenv("BACKEND") or ("mistral" if MISTRAL_API_KEY else "ollama")


def charger_personnalite():
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Modelfile")
    with open(chemin, encoding="utf-8") as f:
        contenu = f.read()
    if 'SYSTEM """' not in contenu:
        return ""
    return contenu.split('SYSTEM """', 1)[1].split('"""', 1)[0].strip()


PERSONNALITE = charger_personnalite()

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
    print(f"Backend d'inférence : {BACKEND}", flush=True)
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

        # On formate le prompt pour donner le contexte au modèle
        prompt_final = f"L'utilisateur {pseudo_auteur} te dit : {prompt_utilisateur}"

        # Gestion du mode "expert" si le flag "explique" est détecté dans le message de l'utilisateur
        system_prompt = ""
        if "explique" in prompt_utilisateur.lower():
            system_prompt = CONSIGNE_EXPERT
            print(f"🧠 Sinj passe en mode Expert pour {pseudo_auteur}", flush=True)

        async with message.channel.typing():
            try:
                def faire_requete():
                    if BACKEND == "mistral":
                        messages = []
                        if PERSONNALITE:
                            messages.append({"role": "system", "content": PERSONNALITE})
                        if system_prompt:
                            messages.append({"role": "system", "content": system_prompt})
                        messages.append({"role": "user", "content": prompt_final})
                        return requests.post(
                            MISTRAL_URL,
                            json={
                                "model": MISTRAL_MODEL,
                                "messages": messages,
                                "temperature": 0.7,
                                "top_p": 0.8,
                            },
                            headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                            timeout=300,
                        )
                    donnees = {
                        "model": MODEL_NAME,
                        "prompt": prompt_final,
                        "stream": False
                    }
                    if system_prompt:
                        donnees["system"] = system_prompt
                    return requests.post(OLLAMA_URL, json=donnees, timeout=300)

                requete = await asyncio.to_thread(faire_requete)

                if requete.status_code == 200:
                    reponse_json = requete.json()
                    if BACKEND == "mistral":
                        replique_bot = reponse_json["choices"][0]["message"]["content"] or "J'ai buggé, saboteur. 💀"
                    else:
                        replique_bot = reponse_json.get("response", "J'ai buggé, saboteur. 💀")
                    await message.reply(replique_bot)
                else:
                    await message.reply("Ollama répond pas, gros saboteur. 🫠‍💨")

            except Exception as erreur:
                print(f"Erreur système : {erreur}", flush=True)
                await message.reply("Erreur de connexion avec mon cerveau. 💀")

client.run(DISCORD_TOKEN)
