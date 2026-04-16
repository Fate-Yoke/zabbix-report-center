@echo off
chcp 65001 >nul
title Zabbix Report Center - Docker 部署

echo ==========================================
echo   Zabbix Report Center - Docker 部署
echo ==========================================

:: 检查 Docker 是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)

:: 检查必要文件是否存在
if not exist docker-compose.yml (
    echo 错误: docker-compose.yml 不存在
    echo 请先复制 docker-compose.yml.example 为 docker-compose.yml 并根据实际情况修改
    pause
    exit /b 1
)

if not exist .env (
    echo 错误: .env 不存在
    echo 请先复制 .env.example 为 .env 并根据实际情况修改
    pause
    exit /b 1
)

:: 构建并启动
echo.
echo 构建并启动容器...
docker-compose up -d --build

echo.
echo ==========================================
echo   部署完成！
echo ==========================================
echo.
echo 访问地址: http://localhost:37201
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f app
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo.
pause
