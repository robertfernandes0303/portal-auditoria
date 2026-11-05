@echo off
cd /d "%~dp0"
git add -A
git -c user.name="Robert Fernandes" -c user.email="robert.fernandes@isssl.com.br" commit -m "Relatorio por visita com dados reais e abertura unidade formulario grupo"
git remote remove origin
git remote add origin https://github.com/robertfernandes0303/portal-auditoria.git
git push -u origin main
echo.
echo Concluido. Pode fechar esta janela.
pause
