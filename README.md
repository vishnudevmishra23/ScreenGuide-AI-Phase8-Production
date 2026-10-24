# ScreenGuide AI — Phase 8

**An AI-powered screen-sharing assistant for visual guidance and real-time interaction.**

ScreenGuide AI is a screen-sharing assistant designed to help users understand on-screen content through screenshot-based visual guidance, voice interaction, and AI-assisted task planning.

## ✨ Features

- **AI-assisted task planning** — Dynamic planning using a vision model.
- **Visual guidance** — Screenshot-based analysis to help users understand screen content.
- **Screen sharing** — Share and analyze on-screen content.
- **Real-time communication** — WebSocket foundation for agent communication.
- **Voice interaction** — Voice input and speech output.
- **Authentication** — JWT-based authentication and bcrypt password hashing.
- **Database persistence** — SQLAlchemy with SQLite support and PostgreSQL configuration.
- **Session history** — Session recording and replay support.
- **Dashboard** — User interface for dashboard, history, and admin/team workflows.

## 🛠️ Technology Stack

- **Backend:** Python, FastAPI
- **Database layer:** SQLAlchemy, SQLite, PostgreSQL-ready configuration
- **Authentication:** JWT, bcrypt
- **Communication:** WebSockets
- **AI integration:** Vision-model-based task planning
- **Frontend:** HTML, CSS, JavaScript

## 📁 Project Structure

```text
ScreenGuide-AI-Phase8-Production/
├── backend/
│   ├── main.py
│   ├── automation.py
│   ├── requirements.txt
│   └── frontend/
├── frontend/
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or a compatible version supported by the dependencies
- Git
- Required AI API credentials

### 1. Clone the repository

```bash
git clone https://github.com/vishnudevmishra23/ScreenGuide-AI-Phase8-Production.git
cd ScreenGuide-AI-Phase8-Production
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local environment configuration using `.env.example` as a reference. Set the actual variable names required by the backend, including your AI provider API key and a strong random JWT secret.

Keep real credentials out of Git and never commit them to the repository.

### 5. Start the backend

From the `backend` directory, run:

```bash
uvicorn main:app --reload
```

When the server starts successfully, open:

- API health check: `http://127.0.0.1:8000/api/health`
- API documentation: `http://127.0.0.1:8000/docs`

Open the frontend using the route or local serving method configured by the project.

## ⚙️ Database Configuration

SQLite is supported by default. PostgreSQL can be configured using the database URL expected by the application.

Example format:

```text
postgresql+psycopg2://USER:PASSWORD@HOST:5432/screenguide
```

Replace the placeholders with your own database details. Never commit real database credentials.

## 🔐 Security Notes

- Store API keys and secrets in local environment variables.
- Keep `.env` files out of version control.
- Use a strong, randomly generated JWT secret.
- Use HTTPS in deployed environments where browser screen sharing requires a secure context.
- Configure appropriate CORS restrictions before deployment.
- Protect session recordings and any stored user data.

## 🗺️ Roadmap

Potential future improvements:

- Automated testing and continuous integration
- Deployment configuration and monitoring
- Improved documentation and troubleshooting
- Additional accessibility and user-experience enhancements

## 👨‍💻 Author

**Vishnu Dev Mishra**

GitHub: [@vishnudevmishra23](https://github.com/vishnudevmishra23)

## 📄 License

No license has been specified yet. Add a license file if you intend to define how others may use, modify, and distribute this project.
