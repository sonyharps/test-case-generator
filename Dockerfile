FROM python:3.11-slim

# Fix timezone
ENV TZ=Asia/Jakarta

# Install OS deps needed by WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libcairo2 \
    libcairo2-dev \
    libgobject-2.0-0 \
    libglib2.0-0 \
    libjpeg62-turbo \
    libpng-dev \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    shared-mime-info \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
