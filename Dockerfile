FROM python:3.12.4-alpine3.20

# Copy Files
RUN mkdir /app
COPY . /app/

# install alpine requirements
RUN apk add --no-cache --virtual .build-deps musl-dev gcc cups-dev \
&& rm -rf /var/cache/apk/*

# Install python requirements
RUN pip3 install -r /app/requirements

# Start
WORKDIR /app
CMD ["python3", "entrypoint.py"]
