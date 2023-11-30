# 需要在之前执行下面两句
# 1. docker build -t ai-agent-base -f init .
# 2. docker tag ai-agent-base ai-base:v1.0
FROM ai-base:v1.0

ENV APPNAME='skg-script'
ENV API_VERESION=v1.0
ENV PYTHONPATH=/app
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION "python"


COPY . /app
WORKDIR /app

CMD ["python","app.py"]
