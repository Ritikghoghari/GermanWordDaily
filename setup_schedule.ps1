$User = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Action = New-ScheduledTaskAction -Execute "d:\Protfolio_Website\GermanWordDaily\run_daily.bat"
$Trigger = New-ScheduledTaskTrigger -Daily -At 9am
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName "GermanWordDaily" -Description "Shows a random German word everyday at 9 AM" -User $User

Write-Host "Task 'GermanWordDaily' has been scheduled for daily at 9:00 AM."
Write-Host "You can verify this in the 'Task Scheduler' app."
