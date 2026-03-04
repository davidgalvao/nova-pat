# Use uma imagem oficial do Python baseada no Debian 12 "bookworm" como imagem base.
FROM python:3.12-slim-bookworm

RUN useradd wagtail

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PORT=8000

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

RUN pip install "gunicorn==20.0.4"

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /code

RUN chown wagtail:wagtail /code

# Copia o código-fonte e o entrypoint para a imagem
COPY --chown=wagtail:wagtail . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown wagtail:wagtail /entrypoint.sh

USER wagtail

# OBS: collectstatic removido do build para evitar assets desatualizados durante o desenvolvimento.
# Use COLLECTSTATIC=1 em tempo de execução (entrypoint) quando necessário.

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
