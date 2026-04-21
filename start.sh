#!/bin/bash

# Zabbix Report Center Docker 启动脚本

echo "=========================================="
echo "  Zabbix Report Center - Docker 部署"
echo "=========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查必要文件是否存在
if [ ! -f docker-compose.yml ]; then
    echo "错误: docker-compose.yml 不存在"
    echo "请先复制 docker-compose.yml.example 为 docker-compose.yml 并根据实际情况修改"
    exit 1
fi

if [ ! -f .env ]; then
    echo "错误: .env 不存在"
    echo "请先复制 .env.example 为 .env 并根据实际情况修改"
    exit 1
fi

# 构建并启动
echo ""
echo "构建并启动容器..."
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "访问地址: http://localhost:38204"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f app"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
