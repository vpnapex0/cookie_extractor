# ... (lines before)
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
    # REMOVED: libxshmfence6 \  <--- DELETE THIS LINE
    libxss1 \
    libxtst6 \
    libu2f-udev \
    fonts-liberation \
    libappindicator1 \
    libnss3-tools \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*
# ... (lines after)
