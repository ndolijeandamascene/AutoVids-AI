# AutoVids AI: AI-Powered "Did You Know?" Content Automation Platform

AutoVids AI is a complete Django-based platform that automates the creation and uploading of viral "Did You Know?" videos for TikTok and other short-form video platforms. It uses AI to generate facts, scripts, voiceovers, and subtitles, then composites them into engaging videos and schedules them for upload, all while simulating safe human behavior.

## 🚀 Key Features

*   **Content Intelligence Engine:**
    *   Generates surprising facts using OpenAI, Anthropic, or Google Gemini.
    *   **Hook Rotation:** Automatically rotates hook styles (Curiosity, Shock, Question) to avoid repetition.
    *   **Duplicate Detection:** Prevents reusing facts or similar content.
*   **Media Engine:**
    *   **AI Voiceovers:** Uses ElevenLabs or Google TTS for high-quality voiceovers.
    *   **Video Composition:** Automatically adds background videos, subtitles, and music.
    *   **Smart Selection:** Intelligently selects backgrounds and voices to ensure variety.
*   **Safe Automation:**
    *   **Human Behavior Simulation:** Mimics human browsing patterns (pauses, mouse movements) to avoid bot detection.
    *   **Risk Management:** Tracks account health and pauses activity if risk score is high.
    *   **Automated Scheduling:** Schedules uploads at optimal times with random variations.
*   **Comprehensive Dashboard:**
    *   Track video performance, account status, and system logs.
    *   Manage content categories, hooks, and background assets.

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
