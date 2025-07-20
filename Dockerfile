# Use a slim Python 3.10 image based on Debian Bullseye
# This must be the VERY FIRST line in your Dockerfile
FROM python:3.10-slim-bullseye

# Install system dependencies required by Chromium for Playwright.
# These are the same dependencies 'playwright install-deps' tries to get.
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    fontconfig \
    locales \
    gconf-service \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libgbm1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpangocairo-1.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libu2f-udev \
    fonts-liberation \
    libappindicator1 \
    libnss3-tools \
    lsb-release \
    xdg-utils \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium).
# This downloads the browser binaries into Playwright's default cache within the container.
RUN python -m playwright install chromium

# Copy the rest of your application code into the container
COPY . .

# Expose the port your FastAPI app will listen on. Render will map this to an external port.
EXPOSE 8000

# Define the command to run your FastAPI application when the container starts.
CMD ["uvicorn", "twitter_cookie_extractor:app", "--host", "0.0.0.0", "--port", "8000"]
