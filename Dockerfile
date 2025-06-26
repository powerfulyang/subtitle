FROM python:3.13-slim

WORKDIR /app

COPY . /app

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]