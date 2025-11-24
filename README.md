# Company Research Assistant (Account Plan Generator)

This is a small demo conversational agent (chat) that helps research companies and generate account plans.

Features:
- Search and fetch info from Wikipedia and DuckDuckGo search results
- Synthesize findings into an account plan (Overview, Financials, Opportunities, Risks, Strategy)
- Detect conflicting facts and ask the user whether to dig deeper
- Allow the user to update specific sections of the generated account plan via chat commands

Quick start

1. Create a Python environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the server:

```bash
uvicorn app:app --reload --port 8000
```

3. Open http://localhost:8000 in your browser and chat with the agent. Start with: `Research <company name>`

Notes
- This demo uses simple web scraping and heuristics for synthesis. It is intended as a demonstration, not a production system.
- If a requested Wikipedia page isn't found, the agent falls back to DuckDuckGo search results.

Files of interest
- `app.py` - FastAPI server + chat API
- `agent/research.py` - research and synthesis logic
- `static/index.html` - frontend chat UI

Voice (optional)

The dashboard includes a client-side voice assistant using the browser's Web Speech APIs:
- Click the microphone button next to the input to start voice input (STT). The transcript will populate the input and final phrases auto-send.
- Agent replies are read aloud using the browser's SpeechSynthesis (TTS).

TTS controls

- Toggle voice replies using the 🔊 button in the header. When enabled, the agent will speak replies and conflict notifications.
- Use the "Read" button on any plan section to have the agent read that section aloud.
- Use the "Read All" button in the Account Plan header to have the agent read the full plan sequentially.

Diagnostics

- If TTS doesn't speak, open the diagnostics page at `/static/diagnostics.html` (link available in the dashboard header). The diagnostics page lists browser voices and provides test-speak controls.
- If no voices are listed, interact with the page (click the TTS toggle) and press "Refresh Voices".



Notes:
- Browser support: Chrome / Edge and modern Chromium browsers support the Web Speech API; Safari support is partial.
- Server-side STT (e.g., Whisper) can be added if you need audio uploads or better language coverage.

