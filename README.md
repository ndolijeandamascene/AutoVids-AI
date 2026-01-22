# AutoVids AI: AI-Powered "Did You Know?" Content Automation Platform

This Django-based system is an AI-powered automation platform designed to grow TikTok accounts by generating short, high-retention “Did You Know?” videos safely and consistently. It uses multiple AI providers to generate unique, curiosity-driven facts, rotates hooks to avoid repetition, converts scripts into natural-sounding voiceovers, and automatically creates vertical videos with captions and varied backgrounds. 

A scheduling and safety layer built with **Celery** and **Redis** controls posting frequency, enforces daily limits, introduces random human-like delays, and respects account age to minimize ban risk. Video uploads are handled exclusively through browser automation using **Playwright** with saved login sessions—no unofficial TikTok APIs or passwords are stored—making the system more stable and secure. 

All configuration is managed via environment variables, and Django provides a central admin/dashboard for monitoring content generation, uploads, and logs, ensuring the platform is scalable, maintainable, and production-ready.

## 🛠️ Technology Stack

*   **Backend:** Django 6.0, Python 3.14
*   **Database:** SQLite (Dev) / PostgreSQL (Prod)
*   **Task Queue:** Celery + Redis
*   **Browser Automation:** Playwright
*   **Video Processing:** MoviePy, OpenCV
*   **AI APIs:** OpenAI, Anthropic, Google Gemini, ElevenLabs

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd AutoVids AI
    ```

2.  **Create virtual environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    # source venv/bin/activate  # Linux/Mac
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

4.  **Set up environment variables:**
    *   Copy `.env.example` to `.env`
    *   Add your API keys (OpenAI, ElevenLabs, etc.)

5.  **Run migrations:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

6.  **Create superuser:**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```

## 🔧 Worker Setup (Required for Automation)

You need to run Celery workers to handle content generation and video processing in the background.

**Start Celery Worker:**
```bash
celery -A autovids_project worker --loglevel=info -P solo
```

**Start Celery Beat (Scheduler):**
```bash
celery -A autovids_project beat --loglevel=info
```

*Note: You need Redis installed and running for Celery to work.*

## 📋 Usage Guide

1.  **Dashboard:** Go to `http://127.0.0.1:8000/dashboard/` to access the main interface.
2.  **Add Assets:**
    *   Upload background videos in the Admin panel (`/admin/media_engine/backgroundvideo/`).
    *   Configure voice profiles (`/admin/media_engine/voiceprofile/`).
3.  **Configure Accounts:**
    *   Add TikTok accounts in the Admin panel.
    *   Enable automation once the account is ready.
4.  **Sit Back:** The system will automatically generate content, create videos, and schedule uploads based on your settings.

## 🛡️ Safety Warning

Automation always carries risks. This system includes extensive safety features (human behavior simulation, random delays, risk monitoring), but you use it at your own risk. Start slow with new accounts.
