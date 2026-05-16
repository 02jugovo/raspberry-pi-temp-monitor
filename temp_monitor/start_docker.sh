#!/bin/bash
# 启动Docker容器的便捷脚本

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "Docker未安装，请先安装Docker"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose未安装，请先安装docker-compose"
    exit 1
fi

# 构建并启动容器
echo "正在构建Docker镜像..."
docker-compose build

echo "正在启动服务..."
docker-compose up -d

echo "服务已启动，访问 http://localhost:5000 查看"
echo "查看日志: docker-compose logs -f"
