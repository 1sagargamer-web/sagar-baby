# Hugging Face Space ke liye: sirf ye ek file Space mein paste karni hai.
# Code apne aap GitHub (main branch) se aata hai.
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 git && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH HF_HOME=/home/user/.cache/huggingface PYTHONUNBUFFERED=1
WORKDIR /home/user/app
ADD --chown=user https://raw.githubusercontent.com/1sagargamer-web/sagar-baby/main/voice-server/requirements.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt
ADD https://api.github.com/repos/1sagargamer-web/sagar-baby/commits/main /tmp/version.json
RUN git clone --depth 1 https://github.com/1sagargamer-web/sagar-baby.git /tmp/src && cp -r /tmp/src/voice-server/. . && rm -rf /tmp/src
EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
