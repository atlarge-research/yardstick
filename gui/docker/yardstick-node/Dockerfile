FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/opt/nvm_home
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless python3 rsync wget curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/nvm_home
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.2/install.sh | bash \
    && . /opt/nvm_home/.nvm/nvm.sh && nvm install 18
RUN chmod -R 777 /opt/nvm_home
RUN ln -sf /usr/bin/python3 /usr/bin/python
CMD ["tail", "-f", "/dev/null"]
