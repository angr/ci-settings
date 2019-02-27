FROM ubuntu:xenial
USER root

# Bootstrap environment
RUN dpkg --add-architecture i386
RUN apt update
RUN apt install -y sudo
RUN useradd --create-home --shell /bin/bash user
RUN usermod -aG sudo user
RUN echo '%sudo   ALL=(ALL:ALL) NOPASSWD:ALL' >> /etc/sudoers

WORKDIR /home/user
USER user
RUN git clone https://github.com/rhelmot/ci-settings.git
RUN ./ci-settings/scripts/latest_deps.sh
