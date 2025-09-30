# auto-mcs Docker Image - Quick Reference

**Maintained by**: [Kaleb Efflandt](https://github.com/macarooni-man)

**Supported tags and architectures**:

- Tags: `latest`, `beta`, any release version
- Architectures: `amd64`, `arm64`

**Image source**:

- Docker Hub: [macarooniman/auto-mcs](https://hub.docker.com/r/macarooniman/auto-mcs/tags)

<br><br>

# How to Use This Image

Although optional, our Docker image (and headless mode) is meant as a minimal feature case to host our custom remote management solution, Telepath, and connect from another device using the GUI. You can learn more about the Telepath API [on our website](https://auto-mcs.com/guides/telepath).

Otherwise, by using this image as a standalone server, you'll still be able to create any server, tunnel through our playit.gg integration, or edit the "server.properties" file. A Telepath connection is required to add worlds, mods/plug-ins, utilize the custom scripting language, and a lot more useful and advanced functionality.

<br><br>

## Command Reference

auto-mcs headless uses commands to interact with it. Once opened, it will bring you to a prompt. Pressing `?` at any time will show help for the current command, or sub-command. To set up a basic Paper server, enter the following commands:

`server create paper:latest My Server`

`server launch My Server`

You can press `ESC` to detach from the console and create or launch other servers. To view auto-mcs commands for Minecraft, type `!help` in the console.

To go back to a server console, you can use the `console` command.

You can also launch auto-mcs with the `--launch` or `-l` flag to start a server automatically:

`auto-mcs --launch "My Server, Server 2"`

<br><br>

## Running the Container

### Basic Usage

To run auto-mcs with default settings:

```bash
env WEB_PORT=8080 WEB_USERNAME='root' WEB_PASSWORD='auto-mcs' \
sh -c 'docker run -d --name auto-mcs \
  -e WEB_PORT -e WEB_USERNAME -e WEB_PASSWORD \
  -p "$WEB_PORT:$WEB_PORT" -p 7001:7001 -p 25565:25565 \
  -v auto-mcs-data:/root/.auto-mcs \
  --restart unless-stopped \
  macarooniman/auto-mcs:latest'
```

This command:

- Runs auto-mcs in a container
- Exposes key ports:
  - `8080` for the TTYD terminal (web interface)
  - `7001` for the Telepath API
  - `25565` for the default port of a Minecraft server
- Stores data in a Docker volume named `auto-mcs-data`
- Secures the TTYD instance using the following credentials:
  - **Username**: `root`
  - **Password**: `auto-mcs`

- ⚠️ In order to use this image, you'll have to change the default credentials. To do so, simply modify the `WEB_USERNAME` and `WEB_PASSWORD` parameters with the desired credentials.
  - Example: `WEB_USERNAME='U$ern4me' WEB_PASSWORD='P@s$w0rd'`

Note that binary of both auto-mcs and ttyd are pre-compiled for optimal compatibility. If you'd like to build these from source, please reference the guide below.

<br>

### Using Docker Compose

To manage auto-mcs with Docker Compose, create a `docker-compose.yml`:

```yaml
version: "3"
services:
  app:
    image: macarooniman/auto-mcs:latest
    container_name: auto-mcs
    stdin_open: true
    tty: true
    restart: unless-stopped

    environment:

      # Default web interface port
      WEB_PORT: "8080"

      # Change the web interface credentials
      WEB_USERNAME: "root"
      WEB_PASSWORD: "auto-mcs"

    ports:

      # Web interface (make this the same as WEB_PORT)
      - "8080:8080"

      # Telepath API (auto-mcs)
      - "7001:7001"

      # Add more ports based on the servers you create
      - "25565:25565"

    volumes:
      - auto-mcs-data:/root/.auto-mcs

volumes:
  auto-mcs-data:
```

To run auto-mcs using Docker Compose, in the same directory run:

```bash
docker-compose up -d
```

<br><br>

## Accessing the TTYD Web Interface

After running the container, open your browser and navigate to `http://localhost:8080` for access to the TTYD web-based terminal. The default credentials are:

- **Username**: `root`
- **Password**: `auto-mcs`

- ⚠️ In order to use this image, you'll have to change the default credentials. To do so, simply modify the `WEB_USERNAME` and `WEB_PASSWORD` parameters with the desired credentials.
  - Example: `WEB_USERNAME: 'U$ern4me' WEB_PASSWORD: 'P@s$w0rd'`

<br><br>

## Data Persistence

To ensure your auto-mcs data persists across container restarts, mount a volume:

```bash
docker run -d \
  --name auto-mcs \
  -v auto-mcs-data:/root/.auto-mcs \
  macarooniman/auto-mcs:latest
```

In Docker Compose, the volume is defined as:

```yaml
volumes:
  auto-mcs-data:
```

This volume will store all configuration files, server data, and back-ups.

<br><br>

# Building the Image Locally

Pre-requisites:

- [Clone auto-mcs repo](https://github.com/macarooni-man/auto-mcs)
- [Clone auto-mcs-ttyd repo](https://github.com/macarooni-man/auto-mcs-ttyd)
- [Alpine Linux 3.15](https://dl-cdn.alpinelinux.org/alpine/v3.15/releases/)

After cloning the repositories on Alpine, move to the root of the `auto-mcs` repository and run the following script to build auto-mcs:

```bash
# Install dependencies
apk add python3 py3-pip gcc pangomm-dev pkgconfig python3-dev zlib-dev libffi-dev musl-dev linux-headers mtdev-dev mtdev

# Build auto-mcs
cd build-tools
chmod +x build-docker.sh
./build-docker.sh
```

After building auto-mcs, move to the root of the `auto-mcs-ttyd` repository and run the following script to build auto-mcs-ttyd:

```bash
# Install dependencies
apk add build-base libwebsockets-evlib_uv bsd-compat-headers cmake json-c-dev libuv-dev libwebsockets-dev openssl-dev>3 samurai zlib-dev

# Build auto-mcs-ttyd
mkdir build && cd build
cmake ..
make && make install
mv -f ./ttyd ../../auto-mcs/docker
```

After building these binaries, move to `auto-mcs/docker` and build the Docker image locally with:

```bash
docker build -t yourusername/auto-mcs:latest .
```

If you need to build for different architectures, such as `amd64` or `arm64`, you can use Docker Buildx:

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t yourusername/auto-mcs:latest --push .
```

<br><br>

## Dockerfile Overview

[View the Dockerfile used for this image on our GitHub](https://github.com/macarooni-man/auto-mcs/blob/main/docker/Dockerfile)