"""Task 9 — Ollama vision-model prompt assist.

Thin client around the local Ollama /api/generate endpoint using the
gemma3:4b-vision model. If Ollama is down the client raises
``OllamaUnavailable`` and the UI silently disables the [Suggest prompts]
button for the session — prompt entry stays fully manual, no modals.
"""
