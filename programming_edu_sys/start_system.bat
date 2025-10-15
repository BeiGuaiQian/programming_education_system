# start_system.bat (Windows批处理文件)
@echo off
echo 启动编程教育智能体系统...
cd /d %~dp0
python run_interactive.py
pause