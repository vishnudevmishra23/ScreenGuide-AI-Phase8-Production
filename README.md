# ScreenGuide AI — Phase 8

Production-style architecture for the ScreenGuide AI screen-sharing assistant.

## Included
- JWT authentication
- Secure bcrypt password hashing
- SQLAlchemy persistence
- SQLite default + PostgreSQL-ready `DATABASE_URL`
- Dynamic task planning with the vision model
- Screenshot-based visual guidance
- WebSocket transport foundation for real-time agent communication
- Screen sharing, continuous analysis, visual pointer
- Voice input + speech output
- Session recording/replay
- Dashboard, history, admin/team UI

## Run

### Windows
```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set OPENAI_API_KEY=YOUR_KEY
set JWT_SECRET=YOUR_RANDOM_SECRET
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/frontend/index.html

### Linux/macOS
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=YOUR_KEY
export JWT_SECRET=YOUR_RANDOM_SECRET
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/frontend/index.html

## PostgreSQL
Set:
`DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/screenguide`

## Important
- Keep `OPENAI_API_KEY` only on the server.
- Use HTTPS in deployed environments because browser screen sharing requires a secure context outside localhost.
- Restrict CORS in production.
- Use a strong random JWT secret.
- For production, move recordings from browser object URLs to authenticated object storage.
- The agent only guides the user; it does not autonomously click/type/submit.
