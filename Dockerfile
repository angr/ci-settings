FROM ubuntu:xenial
USER root

# Bootstrap environment
RUN dpkg --add-architecture i386
RUN apt update
RUN apt install -y sudo git
RUN useradd --create-home --shell /bin/bash user
RUN usermod -aG sudo user
RUN echo '%sudo   ALL=(ALL:ALL) NOPASSWD:ALL' >> /etc/sudoers

# initial dependencies - make sure docker layers aren't too big
RUN apt update
RUN apt upgrade -y
RUN apt install -y vim build-essential python3 python3-dev python3-pip python3-setuptools zip git libffi-dev libtool libtool-bin wget automake bison cmake nasm clang libglib2.0-dev socat libc6:i386 libgcc1:i386 libstdc++6:i386 libtinfo5:i386 zlib1g:i386
RUN pip3 install virtualenv pygithub

WORKDIR /home/user
USER user
RUN git clone https://github.com/rhelmot/ci-settings.git
RUN ./ci-settings/scripts/latest_deps.sh
