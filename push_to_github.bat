@echo off
setlocal
echo ========================================================
echo Pushing SupportIQ to https://github.com/suhana2312/supportiq
echo ========================================================
set "PATH=C:\Users\krish\AppData\Local\Programs\MinGit\cmd;%PATH%"

git status
echo.
echo Pushing to GitHub...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo SUCCESS! Repository uploaded to:
    echo https://github.com/suhana2312/supportiq
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo If push failed, please make sure:
    echo 1. You created the repository at https://github.com/new with name "supportiq"
    echo 2. When prompted for credentials, use your GitHub username and Personal Access Token (PAT)
    echo ========================================================
)
pause
