#!/usr/bin/env python3
"""
Docker环境自动化配置脚本
"""
import os
import shutil
import subprocess

def create_docker_environment():
    """创建完整的Docker环境"""
    
    # 1. 创建Dockerfile
    dockerfile_content = '''# 多阶段构建，优化镜像大小
# 阶段1：构建环境
FROM python:3.9-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# 阶段2：运行环境
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-numpy \
    python3-scipy \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd -m -s /bin/bash tempmonitor

# 设置工作目录
WORKDIR /app

# 复制依赖
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache --no-index --find-links=/wheels /wheels/*

# 复制应用代码
COPY --chown=tempmonitor:tempmonitor . .

# 创建数据目录
RUN mkdir -p data logs models && chown -R tempmonitor:tempmonitor /app

# 切换到非root用户
USER tempmonitor

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

EXPOSE 5000

CMD ["python3", "start_system.py"]
'''
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    # 2. 创建docker-compose.yml
    compose_content = '''version: '3.8'

services:
  temp-monitor:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: temperature_monitor
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./models:/app/models
      # 仅在树莓派上需要
      - /sys/bus/w1/devices:/sys/bus/w1/devices:ro
    environment:
      - TZ=Asia/Shanghai
      - PYTHONPATH=/app
      - FLASK_ENV=production
    # 仅在树莓派上需要
    devices:
      - /dev/gpiomem:/dev/gpiomem
    # 添加资源限制
    mem_limit: 512m
    cpus: 0.5
    
  # 可选：添加监控服务
  monitor:
    image: grafana/grafana:latest
    container_name: temp_monitor_grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-storage:/var/lib/grafana
    depends_on:
      - temp-monitor
    
volumes:
  grafana-storage:
'''
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)
    
    # 3. 创建.dockerignore
    dockerignore_content = '''__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv
pip-log.txt
pip-delete-this-directory.txt
.coverage
.pytest_cache/
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store
'''
    
    with open('.dockerignore', 'w') as f:
        f.write(dockerignore_content)
    
    # 4. 创建启动脚本
    start_script = '''#!/bin/bash
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
'''
    
    with open('start_docker.sh', 'w') as f:
        f.write(start_script)
    
    os.chmod('start_docker.sh', 0o755)
    
    print("Docker环境配置完成")
    print("使用 ./start_docker.sh 启动服务")

if __name__ == '__main__':
    create_docker_environment()
