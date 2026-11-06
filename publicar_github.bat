@echo off
cd /d "%~dp0"
git add -A
git commit -m "Descartar visita em andamento (so Administrador)"
git remote remove origin
git remote add origin https://github.com/robertfernandes0303/portal-auditoria.git
git push -u origin main
echo.
echo Concluido. Pode fechar esta janela.
pause
