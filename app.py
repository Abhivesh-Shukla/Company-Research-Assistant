from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from agent import research
import uuid

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')

# Simple in-memory session store
SESSIONS = {}


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


@app.get('/', response_class=HTMLResponse)
async def index():
    return FileResponse('static/index.html')


@app.post('/chat')
async def chat(req: ChatRequest):
    sid = req.session_id or str(uuid.uuid4())
    session = SESSIONS.setdefault(sid, {'history': [], 'plan': None})
    user_msg = req.message.strip()
    session['history'].append({'role': 'user', 'text': user_msg})

    # Commands:
    # Research <company>
    # update section:<SectionName> <content>
    if user_msg.lower().startswith('research '):
        company = user_msg[len('research '):].strip()
        result = research.research_company(company)
        session['plan'] = result['plan']
        session['history'].append({'role': 'agent', 'text': f"Generated account plan for {company}."})
        payload = {
            'session_id': sid,
            'reply': f"I researched {company}. I generated an account plan.\nDetected {len(result['conflicts'])} potential conflicts.",
            'plan': result['plan'],
            'conflicts': result['conflicts'],
            'sources': result['sources']
        }
        # If conflicts, add a clarifying question
        if result['conflicts']:
            payload['follow_up'] = 'I found conflicting facts (e.g., revenue). Should I dig deeper into financial filings or news?'
        return JSONResponse(payload)

    if user_msg.lower().startswith('update section:'):
        try:
            rest = user_msg[len('update section:'):].strip()
            section, content = rest.split(' ', 1)
            if session.get('plan') is None:
                return JSONResponse({'session_id': sid, 'reply': 'No plan in session. Run a Research command first.'})
            if section not in session['plan']:
                return JSONResponse({'session_id': sid, 'reply': f'Section {section} not found. Available: {list(session["plan"].keys())}'})
            session['plan'][section] = content
            return JSONResponse({'session_id': sid, 'reply': f'Section {section} updated.', 'plan': session['plan']})
        except Exception as e:
            return JSONResponse({'session_id': sid, 'reply': 'Could not parse update command. Use: update section:<SectionName> <content>'})

    # Generic reply: echo or show plan
    if user_msg.lower() in ('show plan', 'view plan'):
        if session.get('plan'):
            return JSONResponse({'session_id': sid, 'reply': 'Here is the current plan.', 'plan': session['plan']})
        else:
            return JSONResponse({'session_id': sid, 'reply': 'No plan in session. Try: Research <company>'})

    # Default small-minded agent responses
    return JSONResponse({'session_id': sid, 'reply': 'Sorry, I did not understand. Try: Research <company> or Show Plan or Update Section:<SectionName> <content>'})


if __name__ == '__main__':
    uvicorn.run('app:app', host='127.0.0.1', port=8000, reload=True)
