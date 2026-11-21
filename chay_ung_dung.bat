@echo off
rem FoodReview Insight - chay tren Windows: nhap dup file nay (cua so phai mo trong luc dung ung dung).
rem Chi tim Python 3.10 - 3.12 roi giao cho run_app.py (tao .venv, cai thu vien, chay giao dien + API o mot cong).
setlocal
cd /d "%~dp0"
title FoodReview Insight
set "PYCMD="
if exist ".venv\Scripts\python.exe" set "PYCMD=.venv\Scripts\python.exe"
if not defined PYCMD py -3.11 -c "import sys" >nul 2>&1 && set "PYCMD=py -3.11"
if not defined PYCMD py -3.12 -c "import sys" >nul 2>&1 && set "PYCMD=py -3.12"
if not defined PYCMD py -3.10 -c "import sys" >nul 2>&1 && set "PYCMD=py -3.10"
if not defined PYCMD python -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,12) else 1)" >nul 2>&1 && set "PYCMD=python"
if not defined PYCMD goto nopython
%PYCMD% run_app.py %*
echo.
pause
exit /b 0

:nopython
echo [FoodReview Insight] Khong tim thay Python 3.10 - 3.12 tren may.
echo Cai Python 3.11 tai https://www.python.org/downloads/windows/
echo (khi cai nho tick "Add python.exe to PATH"), roi nhap dup lai file nay.
echo.
pause
exit /b 1
