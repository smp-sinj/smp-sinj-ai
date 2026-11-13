# smp-sinj-ai
IA officielle de la SMP

## Utilisation

Le bot répond sur Discord quand il est mentionné ou quand "sinj" apparaît dans un message.

Deux backends d'inférence au choix :

- **Mistral API (cloud)** : renseigner `MISTRAL_API_KEY` dans `.env` (utilisé automatiquement, sinon poser `BACKEND=mistral`). Modèle par défaut : `mistral-small-latest` (modifiable via `MISTRAL_MODEL`). La personnalité est lue telle quelle dans le `Modelfile` et envoyée en message `system`. Ce backend consomme les crédits API inclus dans l'abonnement Mistral (ex. plan étudiant), sans pay-as-you-go.
- **Ollama local** : sans `MISTRAL_API_KEY`, le bot appelle `OLLAMA_URL` (défaut `http://ollama:11434/api/generate`) avec le modèle `smp-sinj` créé depuis le `Modelfile` (`ollama create smp-sinj -f Modelfile`).

## Déploiement

Push sur `main` : l'action GitHub déploie sur le Pi 5 via Tailscale + docker compose.
