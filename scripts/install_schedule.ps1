<#
.SYNOPSIS
    Registers Windows Task Scheduler jobs for continuous .si domain updates.

.DESCRIPTION
    Provides automated scheduling for:
    1. Daily refresh of the Top 500 opportunities (03:00 UTC)
    2. Weekly comprehensive refresh of the full candidate pool (Sundays at 01:00 UTC)
    
    PER GOAL SPECIFICATION: This script provides the task definitions and registration
    commands, but MUST NOT be executed automatically during build/setup.

.NOTES
    To manually install these tasks as an Administrator, open PowerShell as Admin and run:
    .\scripts\install_schedule.ps1 -Install
#>

param(
    [switch]$Install,
    [switch]$Uninstall
)

$PythonExe = (Get-Command python).Source
$ProjectDir = (Resolve-Path "$PSScriptRoot\..").Path

$DailyTaskName = "SiDomains_Daily_Top500_Refresh"
$WeeklyTaskName = "SiDomains_Weekly_Full_Refresh"

if ($Uninstall) {
    Write-Host "Unregistering scheduled tasks..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $DailyTaskName -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $WeeklyTaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Scheduled tasks unregistered." -ForegroundColor Green
    exit 0
}

if (-not $Install) {
    Write-Host @"
========================================================================
 .si Domain Marketplace - Windows Task Scheduler Setup
========================================================================

This script defines the scheduled tasks required for continuous updates:

1. Daily Top 500 Refresh:
   - Task Name: $DailyTaskName
   - Trigger: Every day at 03:00 AM
   - Action: $PythonExe -m si_domains refresh --limit 500 --min-interval 1.1

2. Weekly Full Pool Refresh:
   - Task Name: $WeeklyTaskName
   - Trigger: Every Sunday at 01:00 AM
   - Action: $PythonExe -m si_domains refresh --min-interval 1.1

To register these tasks on Windows, run this script with -Install as Admin:
    powershell -ExecutionPolicy Bypass -File .\scripts\install_schedule.ps1 -Install

To remove them later:
    powershell -ExecutionPolicy Bypass -File .\scripts\install_schedule.ps1 -Uninstall

NOTE: Under unattended build rules, tasks are NOT installed automatically.
========================================================================
"@
    exit 0
}

Write-Host "Registering $DailyTaskName..." -ForegroundColor Cyan
$DailyAction = New-ScheduledTaskAction -Execute $PythonExe -Argument "-m si_domains refresh --limit 500 --min-interval 1.1" -WorkingDirectory $ProjectDir
$DailyTrigger = New-ScheduledTaskTrigger -Daily -At "03:00"
Register-ScheduledTask -TaskName $DailyTaskName -Action $DailyAction -Trigger $DailyTrigger -Description "Daily refresh of top 500 .si domain availability" -Force

Write-Host "Registering $WeeklyTaskName..." -ForegroundColor Cyan
$WeeklyAction = New-ScheduledTaskAction -Execute $PythonExe -Argument "-m si_domains refresh --min-interval 1.1" -WorkingDirectory $ProjectDir
$WeeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "01:00"
Register-ScheduledTask -TaskName $WeeklyTaskName -Action $WeeklyAction -Trigger $WeeklyTrigger -Description "Weekly full pool refresh of .si domain availability" -Force

Write-Host "All tasks successfully registered!" -ForegroundColor Green
