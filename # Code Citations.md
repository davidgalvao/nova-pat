# Code Citations

## License: desconhecido
https://github.com/aazhbd/quoteshare/tree/7adc7acf1ee7f526b1708b56b50712518632d284/contents/Dockerfile

```
dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

RUN pip install "gunicorn==20.0.4"

COPY requirements.txt /
RUN pip install -r /
```


## License: desconhecido
https://github.com/pycascades/pycascades-cms/tree/aa07a92dece0d51aa947d73d8b37d62df6a95b76/Dockerfile

```
-yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -
```

