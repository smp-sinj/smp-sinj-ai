# smp-sinj-ai
IA officielle de la SMP

## Utilisation

Le bot répond sur Discord quand il est mentionné ou quand "sinj" apparaît dans un message.

Deux backends d'inférence au choix :

- **Mistral API (cloud)** : renseigner `MISTRAL_API_KEY` dans `.env` (utilisé automatiquement, sinon poser `BACKEND=mistral`). Modèle par défaut : `mistral-small-latest` (modifiable via `MISTRAL_MODEL`). La personnalité est lue telle quelle dans le `Modelfile` et envoyée en message `system`. Ce backend consomme les crédits API inclus dans l'abonnement Mistral (ex. plan étudiant), sans pay-as-you-go.
- **Ollama local** : sans `MISTRAL_API_KEY`, le bot appelle `OLLAMA_URL` (défaut `http://ollama:11434/api/generate`) avec le modèle `smp-sinj` créé depuis le `Modelfile` (`ollama create smp-sinj -f Modelfile`).

## Mémoire automatique

Après chaque réponse, le bot fait un second appel au modèle (prompt d'extraction dédié, `temperature 0`, réponse JSON stricte) pour décider **lui-même** si le message contient quelque chose à retenir (nouvelle expression, fait sur un membre, lore...). Si oui, c'est écrit dans `mémoire.md` (ignoré par git, persisté via le volume compose) et réinjecté dans le prompt système à chaque message suivant. Les doublons sont filtrés et le fichier est plafonné à `MAX_MEMOIRES` lignes. Désactivable avec `MEMOIRE_AUTO=false`.

## Déploiement

Push sur `main` : l'action GitHub déploie sur le Pi 5 via Tailscale + docker compose.
