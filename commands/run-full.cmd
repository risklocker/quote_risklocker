@echo off
cd /d "%~dp0.."
start "Risklocker Backend" cmd /k commands\run-backend.cmd
start "Risklocker Frontend" cmd /k commands\run-frontend.cmd
