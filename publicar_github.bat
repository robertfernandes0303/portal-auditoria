@echo off
cd /d "%~dp0"
git remote remove origin 2>nul
git remote add origin https://github.com/robertfernandes0303/portal-auditoria.git
git push -u origin main
pause
