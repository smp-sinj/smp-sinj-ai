# smp-sinj-ai
IA officielle de la SMP

## Utilisation

Le bot répond sur Discord quand il est mentionné ou quand "sinj" apparaît dans un message.

Deux backends d'inférence au choix :

- **Mistral API (cloud)** : renseigner `MISTRAL_API_KEY` dans `.env` (utilisé automatiquement, sinon poser `BACKEND=mistral`). Modèle par défaut : `mistral-small-latest` (modifiable via `MISTRAL_MODEL`). La personnalité est lue telle quelle dans le `Modelfile` et envoyée en message `system`. Ce backend consomme les crédits API inclus dans l'abonnement Mistral (ex. plan étudiant), sans pay-as-you-go.
- **Ollama local** : sans `MISTRAL_API_KEY`, le bot appelle `OLLAMA_URL` (défaut `http://ollama:11434/api/generate`) avec le modèle `smp-sinj` créé depuis le `Modelfile` (`ollama create smp-sinj -f Modelfile`).

## Mémoire automatique

Après chaque réponse, le bot fait un second appel au modèle (prompt d'extraction dédié, `temperature 0`, réponse JSON stricte) pour décider **lui-même** si le message contient quelque chose à retenir (nouvelle expression, fait sur un membre, lore...). Si oui, c'est écrit dans `mémoire.md` (ignoré par git, persisté via le volume compose) et réinjecté dans le prompt système à chaque message suivant. Les doublons sont filtrés et le fichier est plafonné à `MAX_MEMOIRES` lignes. Désactivable avec `MEMOIRE_AUTO=false`.

## Réponses plus développées + contexte

Le persona autorise désormais des réponses développées (~80 mots) quand la question le mérite, tout en gardant le ton cassant (règle 2 du `Modelfile`). Un historique des `HISTORIQUE_MAX` derniers messages du salon (défaut 8, `0` = désactivé) est aussi injecté dans le prompt pour donner du contexte. Pour un modèle plus puissant : `MISTRAL_MODEL=mistral-medium-latest`.

## DNS (Pi-hole)

`sinj-bot` tourne en `network_mode: host` : il utilise directement le `resolv.conf` du Pi (1.1.1.1/9.9.9.9), donc il ne dépend pas de Pi-hole (qui redirige le port 53 des conteneurs mais n'a pas d'upstream configuré → `Temporary failure in name resolution` vers la gateway Discord). `ollama` (optionnel, backend local) garde des DNS fixés 1.1.1.1/9.9.9.9.

Le déploiement GitHub Actions passe par Tailscale : le Pi doit être en ligne et tagué `tag:server` dans le tailnet, avec une ACL `tag:server -> tag:server:22`, et le secret `PI_HOST` doit être son nom ts.net ou son IP 100.x.

## Déploiement

Push sur `main` : l'action GitHub déploie sur le Pi 5 via Tailscale. Le build se fait avec `docker build --network host` (sinon le DNS du conteneur de build est redirigé vers Pi-hole, qui n'a pas d'upstream → le `pip install` échoue) ; le Pi est aligné sur `origin/main` via `git reset --hard` et `set -e` rend le run rouge en cas d'erreur.
