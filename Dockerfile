# Use a slim Python 3.10 image based on Debian Bullseye
# Debian-based images (like 'slim' variants) are common and compatible with Playwright's dependencies.
FROM python:3.10-slim-bullseye

# Install system dependencies required by Chromium for Playwright.
# These are the same dependencies 'playwright install-deps' tries to get.
# Using 'apt-get update' and 'apt-get install -y' during a Docker build runs with root privileges.
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
    libxshmfence6 \
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
# Using --no-cache-dir helps reduce image size
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium).
# Now that system dependencies are handled, this step should succeed fully.
# This downloads the browser binaries into Playwright's default cache path within the container.
RUN python -m playwright install chromium

# Copy the rest of your application code into the container
COPY . .

# Expose the port your FastAPI app will listen on. Render will map this to an external port.
EXPOSE 8000

# Define the command to run your FastAPI application when the container starts.
# Render automatically injects the $PORT environment variable, but for Dockerfiles
# it's common to explicitly listen on a fixed port like 8000, and Render maps to that.
CMD ["uvicorn", "twitter_cookie_extractor:app", "--host", "0.0.0.0", "--port", "8000"]
