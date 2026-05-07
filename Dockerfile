FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Hugging Face Spaces 要求容器以非 root 用户运行
RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

COPY --chown=user . .

# 7860 是 HF Spaces 默认对外端口
EXPOSE 7860

# 启动时先 seed（建表 + 内置角色），再起 uvicorn
CMD python seed.py && uvicorn main:app --host 0.0.0.0 --port 7860
