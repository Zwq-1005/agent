@echo off
echo ========================================
echo  医学统计 AI 助手 - 启动脚本
echo ========================================

REM Start backend
echo [1/2] 启动后端...
start "Backend" cmd /c "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo [2/2] 启动前端...
start "Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo 后端: http://localhost:8000/docs
echo 前端: http://localhost:5173
echo ========================================
