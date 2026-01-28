@echo off
cd /d "%~dp0"
echo %DATE% %TIME% - Starting Quiz >> debug_log_quiz.txt
python german_daily.py --mode quiz >> debug_log_quiz.txt 2>&1
echo %DATE% %TIME% - Finished with code %errorlevel% >> debug_log_quiz.txt
