@echo off
:loop
git add *.py

:: Verifica se há mudanças nos arquivos .py
git diff --cached --quiet
if %ERRORLEVEL% neq 0 (
    git commit -m "Commit automático"
    git push -u origin main --force
)

:: Aguarda 60 segundos antes de verificar novamente
timeout /t 60
goto loop
