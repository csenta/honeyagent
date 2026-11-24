FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

RUN groupadd -r honeyagent && useradd -r -g honeyagent -d /home/honeyagent -m honeyagent
WORKDIR /app

COPY --from=builder /root/.local /home/honeyagent/.local
COPY --chown=honeyagent:honeyagent . /app

ENV PATH=/home/honeyagent/.local/bin:$PATH
ENV PYTHONPATH=/app

USER honeyagent
EXPOSE 8888

ENTRYPOINT ["python3", "-m", "honeyagent.cli"]
CMD ["listen", "--host", "0.0.0.0", "--port", "8888"]
