FROM python:3.11-bullseye

# Install bash
RUN apt-get update && apt-get install -y bash gh

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache -r requirements.txt && \
    python -m playwright install && \
    python -m playwright install-deps && \
    echo eval '$(gh completion -s bash)' >> ~/.bashrc

COPY ./src/*.py /app/

VOLUME /app/data

# Create user and group 1000
RUN groupadd -g 1000 app && \
    useradd -r -u 1000 -g app app

# Change ownership of /app to app:app
RUN chown -R app:app /app

# Change to user app
USER app

CMD ["python", "/app/src/imgur.py"]