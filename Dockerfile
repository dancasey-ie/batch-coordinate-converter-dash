FROM python:3.8.10

WORKDIR usr/src/dash_app
COPY ./dash_app .
RUN pip install --no-cache-dir -r requirements.txt \
    && chmod +x ./entrypoint.sh
ENTRYPOINT ["sh", "entrypoint.sh"]