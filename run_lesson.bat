@echo off
cd /d "%~dp0"
echo %DATE% %TIME% - Starting Lesson >> debug_log_lesson.txt
python german_daily.py --mode lesson --count 10 >> debug_log_lesson.txt 2>&1
echo %DATE% %TIME% - Finished with code %errorlevel% >> debug_log_lesson.txt
