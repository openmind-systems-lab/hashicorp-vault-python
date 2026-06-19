FROM python:3.12-slim

WORKDIR /app
COPY app.py /app/app.py

ENV PORT=8080 \
    VAULT_SECRET_FILE=/vault/secrets/Realm.xml

EXPOSE 8080
CMD ["python", "/app/app.py"]
