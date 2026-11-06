@echo off
cd /d "%~dp0"
git add -A
git -c user.name="Robert Fernandes" -c user.email="robert.fernandes@isssl.com.br" commit -m "Mostra ultimo retrato dos dados na hora e atualiza em segundo plano"
git remote remove origin
git remote add origin https://github.com/robertfernandes0303/portal-auditoria.git
git push -u origin main
echo.
echo Concluido. Pode fechar esta janela.
pause
