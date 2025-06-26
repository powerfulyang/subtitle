# 第一阶段：构建阶段
FROM python:3.10-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖（构建时需要的工具）
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装Python依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装PyTorch (CPU版本)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 安装audio-separator
RUN pip install --no-cache-dir "audio-separator[cpu]"

# 安装其他依赖
RUN pip install --no-cache-dir -r requirements.txt

# 第二阶段：运行阶段
FROM python:3.10-slim AS runtime

# 安装运行时必需的系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 确保使用虚拟环境
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY --chown=app:app . .

# 创建必要的目录并设置权限
RUN mkdir -p uploads temp_separation && \
    chown -R app:app /app

# 切换到非root用户
USER app

# 暴露端口（如果需要）
EXPOSE 8002

# 设置入口点
ENTRYPOINT ["python", "main.py"]