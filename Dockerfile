# 需要在之前执行下面两句
# 1. docker build -t skg-script-base -f init .
# 2. docker tag skg-script-base base:v2.0
FROM skg-script-base:v2.0

ENV APPNAME='skg-script'
ENV API_VERESION=v1.0
ENV PYTHONPATH=/app
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION "python"


COPY . /app
WORKDIR /app

CMD ["gunicorn","-c","config.py","app:agent"]
