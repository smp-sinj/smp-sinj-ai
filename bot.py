import os
import json
import asyncio
import threading
from datetime import datetime, timezone

import discord
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
MODEL_NAME = "smp-sinj"

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_URL = os.getenv("MISTRAL_URL", "https://api.mistral.ai/v1/chat/completions")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
BACKEND = os.getenv("BACKEND") or ("mistral" if MISTRAL_API_KEY else "ollama")

MEMOIRE_FILE = os.getenv("MEMOIRE_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "mémoire.md")
MEMOIRE_AUTO = os.getenv("MEMOIRE_AUTO", "true").lower() in ("1", "true", "oui")
MAX_MEMOIRES = int(os.getenv("MAX_MEMOIRES", "200"))
HISTORIQUE_MAX = int(os.getenv("HISTORIQUE_MAX", "8"))

VERROU_MEMOIRE = threading.Lock()
HISTORIQUE = {}
VERROU_HISTORIQUE = threading.Lock()


def charger_personnalite():
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Modelfile")
    with open(chemin, encoding="utf-8") as f:
        contenu = f.read()
    if 'SYSTEM """' not in contenu:
        return ""
    return contenu.split('SYSTEM """', 1)[1].split('"""', 1)[0].strip()


PERSONNALITE = charger_personnalite()

PROMPT_EXTRACTION = (
    "Tu es un module d'extraction de mémoire pour un bot Discord. "
    "On te fournit un message d'utilisateur, la réponse du bot et les mémoires déjà enregistrées. "
    "Décide si le message contient une information durable et utile à retenir plus tard "
    "(nouvelle expression, fait sur un membre du groupe, préférence, règle, lore). "
    "Si oui, réponds UNIQUEMENT avec un JSON : {\"a_retenir\": true, \"memoire\": \"<phrase courte et factuelle, max 20 mots>\"}. "
    "Si non, réponds UNIQUEMENT avec : {\"a_retenir\": false, \"memoire\": \"\"}. "
    "Ne retiens ni les banalités, ni les données sensibles, et ne retiens pas une information déjà présente dans les mémoires existantes."
)

CONSIGNE_EXPERT = (
    " MAIS ATTENTION : L'utilisateur t'a demandé une explication technique/de cours. "
    "Pour cette réponse précise, tu as l'autorisation de faire un long pavé ultra-détaillé, "
    "mathématique et rigoureux. Ne limite pas tes mots. Par contre, garde ton ton méprisant "
    "et lâche obligatoirement tes expressions fétiches comme 'dégâts dégâts' ou 'saboteur' au milieu de tes explications."
)


def normaliser(texte):
    return " ".join(texte.lower().split())


def lire_memoires():
    if not os.path.exists(MEMOIRE_FILE):
        return ""
    with open(MEMOIRE_FILE, encoding="utf-8") as f:
        return f.read().strip()


def est_deja_en_memoire(texte):
    n = normaliser(texte)
    if not n:
        return True
    return n in normaliser(lire_memoires())


def enregistrer_memoire(texte, auteur):
    ligne = f"- [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC] ({auteur}) {texte}\n"
    with VERROU_MEMOIRE:
        with open(MEMOIRE_FILE, "a", encoding="utf-8") as f:
            f.write(ligne)
        with open(MEMOIRE_FILE, encoding="utf-8") as f:
            lignes = f.readlines()
        if len(lignes) > MAX_MEMOIRES:
            with open(MEMOIRE_FILE, "w", encoding="utf-8") as f:
                f.writelines(lignes[-MAX_MEMOIRES:])


def contexte_recent(channel_id):
    with VERROU_HISTORIQUE:
        hist = list(HISTORIQUE.get(channel_id, []))
    if not hist:
        return ""
    return "Contexte récent du salon :\n" + "\n".join(hist)


def extraire_et_sauvegarder(auteur, message_utilisateur, reponse_bot):
    try:
        memoires = lire_memoires()
        contexte = (
            f"Message de {auteur} : {message_utilisateur}\n"
            f"Réponse du bot : {reponse_bot}\n"
            f"Mémoires existantes :\n{memoires or '(aucune)'}"
        )
        if BACKEND == "mistral":
            payload = {
                "model": MISTRAL_MODEL,
                "messages": [
                    {"role": "system", "content": PROMPT_EXTRACTION},
                    {"role": "user", "content": contexte},
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
            }
            requete = requests.post(
                MISTRAL_URL,
                json=payload,
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                timeout=60,
            )
            if requete.status_code != 200:
                return
            brut = requete.json()["choices"][0]["message"]["content"]
        else:
            payload = {
                "model": MODEL_NAME,
                "prompt": f"{PROMPT_EXTRACTION}\n\n{contexte}",
                "stream": False,
                "format": "json",
            }
            requete = requests.post(OLLAMA_URL, json=payload, timeout=60)
            if requete.status_code != 200:
                return
            brut = requete.json().get("response", "")
        try:
            donnees = json.loads(brut)
        except (json.JSONDecodeError, TypeError):
            return
        if donnees.get("a_retenir") and donnees.get("memoire"):
            texte = str(donnees["memoire"]).strip()
            if texte and not est_deja_en_memoire(texte):
                enregistrer_memoire(texte, auteur)
                print(f"🧠 Mémoire enregistrée ({auteur}) : {texte}", flush=True)
    except Exception as erreur:
        print(f"Mémoire non enregistrée : {erreur}", flush=True)


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🔥 Sinj AI est en ligne sous le pseudo : {client.user}", flush=True)
    print(f"Backend d'inférence : {BACKEND}", flush=True)
    print(f"Mémoire auto : {'activée' if MEMOIRE_AUTO else 'désactivée'} -> {MEMOIRE_FILE}", flush=True)
    print("Prêt à cibler ses victimes sur le serveur. 💀", flush=True)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if HISTORIQUE_MAX > 0:
        with VERROU_HISTORIQUE:
            hist = HISTORIQUE.setdefault(message.channel.id, [])
            hist.append(f"{message.author.display_name}: {message.content[:200]}")
            while len(hist) > HISTORIQUE_MAX:
                hist.pop(0)

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

        memoires = lire_memoires()
        contexte = contexte_recent(message.channel.id)

        async with message.channel.typing():
            try:
                def faire_requete():
                    if BACKEND == "mistral":
                        messages = []
                        if PERSONNALITE:
                            messages.append({"role": "system", "content": PERSONNALITE})
                        if memoires:
                            messages.append({"role": "system", "content": f"Mémoires apprises jusqu'ici (utilise-les si pertinent) :\n{memoires}"})
                        if contexte:
                            messages.append({"role": "system", "content": contexte})
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
                        "prompt": (f"Mémoires apprises jusqu'ici :\n{memoires}\n\n" if memoires else "") + (contexte + "\n\n" if contexte else "") + prompt_final,
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
                    if MEMOIRE_AUTO:
                        await asyncio.to_thread(extraire_et_sauvegarder, pseudo_auteur, prompt_utilisateur, replique_bot)
                else:
                    await message.reply("Ollama répond pas, gros saboteur. 🫠‍💨")

            except Exception as erreur:
                print(f"Erreur système : {erreur}", flush=True)
                await message.reply("Erreur de connexion avec mon cerveau. 💀")

client.run(DISCORD_TOKEN)
