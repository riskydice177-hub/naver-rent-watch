# 매일 지정 시각에 main.py를 자동 실행하도록 Windows 작업 스케줄러에 등록합니다.
# 사용법:  powershell -ExecutionPolicy Bypass -File schedule.ps1 -Time 08:30
# 해제:    Unregister-ScheduledTask -TaskName NaverRentWatch -Confirm:$false
param([string]$Time = "08:30")

$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$action = New-ScheduledTaskAction -Execute $python -Argument "main.py" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "NaverRentWatch" -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "등록 완료: 매일 $Time 에 실행 (PC가 꺼져 있었다면 켜진 뒤 실행)"
