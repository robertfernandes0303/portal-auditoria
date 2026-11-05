@echo off
cd /d "%~dp0"
git add -A
git -c user.name="Robert Fernandes" -c user.email="robert.fernandes@isssl.com.br" commit -m "Painel: filtro multiplo de unidades, leitura paralela, resumo de conexoes, rolagem do mouse"
git remote remove origin
git remote add origin https://github.com/robertfernandes0303/portal-auditoria.git
git push -u origin main
echo.
echo Concluido. Pode fechar esta janela.
pause
