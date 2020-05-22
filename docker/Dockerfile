FROM ubuntu:bionic
USER root
WORKDIR /root
RUN chmod 755 .

# install deps. make sure not to create too-large layers
RUN dpkg --add-architecture i386
RUN apt-get update
RUN apt-get install -y vim build-essential python3 python3-dev python3-pip python3-setuptools zip git libffi-dev libtool libtool-bin wget automake bison cmake nasm clang socat
RUN apt-get install -y libglib2.0-dev libc6:i386 libgcc1:i386 libstdc++6:i386 libtinfo5:i386 zlib1g:i386
RUN apt-get install -y gdb gdbserver openjdk-8-jdk-headless
RUN pip3 install "virtualenv<20" pygithub

RUN umask 0; git clone https://github.com/angr/wheels.git
ADD scripts ./scripts
ADD conf ./conf
ENTRYPOINT ["/root/scripts/entrypoint.sh"]
