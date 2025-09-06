@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    🤖 Запуск Telegram бота
echo ========================================
echo.

REM Активируем виртуальное окружение
call venv\Scripts\activate.bat

REM Запускаем бота
python telegram_bot.py

pause
