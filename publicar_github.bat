@echo off
cd /d "%~dp0"
git add -A
git commit -m "SESMT, plano de acao por quem acompanhou, visitas em aberto somente consulta, cidade/UF automaticas e cache nas visitas tecnicas"
git remote remove origin
git remote add origin https://github.com/robertfernandes0303/portal-auditoria.git
git push -u origin main
echo.
echo Concluido. Pode fechar esta janela.
pause
