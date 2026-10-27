FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Train the model at build time so the image is self-contained
RUN python -m ml.train
RUN useradd -m app && mkdir -p instance && chown -R app /srv
USER app
EXPOSE 5000
HEALTHCHECK CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:5000/api/v1/health')" || exit 1
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:create_app()"]
