$User = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# --- Task 1: Lesson (Every 1 Hour) ---
$ActionLesson = New-ScheduledTaskAction -Execute "d:\Protfolio_Website\GermanWordDaily\run_lesson.bat"
# Trigger: Once at 12:00 AM, but repeat every 1 hour for 1000 days (effectively forever)
$TriggerLesson = New-ScheduledTaskTrigger -Once -At "12:00 AM" -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365)

if (Get-ScheduledTask -TaskName "GermanWordDaily" -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName "GermanWordDaily" -Confirm:$false
}
Register-ScheduledTask -Action $ActionLesson -Trigger $TriggerLesson -Settings $Settings -TaskName "GermanWordDaily" -Description "German Word Lesson (Every Hour)" -User $User

# --- Task 2: Quiz (Every 1 Hour) ---
$ActionQuiz = New-ScheduledTaskAction -Execute "d:\Protfolio_Website\GermanWordDaily\run_quiz.bat"
# Trigger: Same schedule
$TriggerQuiz = New-ScheduledTaskTrigger -Once -At "12:00 AM" -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365)

if (Get-ScheduledTask -TaskName "GermanWordQuiz" -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName "GermanWordQuiz" -Confirm:$false
}
Register-ScheduledTask -Action $ActionQuiz -Trigger $TriggerQuiz -Settings $Settings -TaskName "GermanWordQuiz" -Description "German Quiz (Every Hour)" -User $User

Write-Host "Schedule Updated to HOURLY:"
Write-Host "1. 'GermanWordDaily' -> Every 1 Hour (Lesson)"
Write-Host "2. 'GermanWordQuiz'  -> Every 1 Hour (Quiz)"
