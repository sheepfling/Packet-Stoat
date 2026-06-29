FROM grill-linux-proof:ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y \
        cmake \
        build-essential \
        libglib2.0-0 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxrandr2 \
        libxinerama1 \
        libxcursor1 \
        libxi6 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxext6 \
        libsm6 \
        libice6 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libatspi2.0-0 \
        libasound2t64 \
        libcairo2 \
        libfontconfig1 \
        libfreetype6 \
        libnss3 \
        libdbus-1-3 \
        libpango-1.0-0 \
        libdrm2 \
        libgbm1 \
        libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*
