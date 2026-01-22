@echo off
call venv\Scripts\activate.bat
echo Starting AutoVids AI Server...
echo Access Dashboard at http://127.0.0.1:8000/dashboard/
echo Login with: admin / admin
python manage.py runserver
