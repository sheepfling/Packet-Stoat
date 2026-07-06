FROM fastdis-linux-proof:ubuntu24.04

ARG GODOT_VERSION=4.7
ARG GODOT_CHANNEL=stable
ARG GODOT_ZIP=Godot_v${GODOT_VERSION}-${GODOT_CHANNEL}_linux.x86_64.zip
ARG GODOT_DOWNLOAD_URL=https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-${GODOT_CHANNEL}/${GODOT_ZIP}

ENV DEBIAN_FRONTEND=noninteractive
ENV FASTDIS_GODOT_ROOTS=/usr/local/bin:/opt/godot
ENV FASTDIS_SCONS=/usr/bin/scons

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        unzip \
        python3 \
        python3-pip \
        scons \
        git \
        pkg-config \
        cmake \
        ninja-build \
        build-essential \
        g++ \
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

RUN mkdir -p /opt/godot \
    && curl --fail --location --retry 3 --output /tmp/godot.zip "${GODOT_DOWNLOAD_URL}" \
    && unzip -q /tmp/godot.zip -d /opt/godot \
    && rm /tmp/godot.zip \
    && find /opt/godot -maxdepth 1 -type f -name 'Godot*_linux.x86_64' -exec chmod +x {} \; -exec ln -sf {} /usr/local/bin/godot \; \
    && godot --version \
    && scons --version
