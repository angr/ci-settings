FROM ubuntu:22.04
ENV DEBIAN_FRONTEND noninteractive
USER root
WORKDIR /root
RUN chmod 755 .

# install deps. make sure not to create too-large layers
RUN dpkg --add-architecture i386
RUN apt-get update
RUN apt-get install -y vim build-essential python3 python3-dev python3-pip python3-setuptools zip git libffi-dev libtool libtool-bin wget automake bison cmake nasm clang socat lld
RUN apt-get install -y libglib2.0-dev libreadline-dev libc6:i386 libgcc1:i386 libstdc++6:i386 libtinfo5:i386 zlib1g:i386
RUN apt-get install -y libc6-armhf-cross libc6-arm64-cross libc6-mips-cross libc6-mips64-cross libc6-powerpc-cross libc6-powerpc-ppc64-cross
RUN apt-get install -y gdb gdbserver gdb-multiarch openjdk-8-jdk-headless docker.io libgl1
RUN apt-get install -y binutils-mips-linux-gnu binutils-mipsel-linux-gnu binutils-arm-linux-gnueabi
RUN apt-get install -y strace
RUN apt-get install -y fontconfig
RUN apt-get install -y gcc-multilib g++-multilib
RUN apt-get install -y libxkbcommon-dev libegl-dev
RUN apt-get install -y zstd
RUN pip3 install "virtualenv<20" pygithub

# fix missing libreadline.so.7
RUN ln -s /lib/x86_64-linux-gnu/libreadline.so /lib/x86_64-linux-gnu/libreadline.so.7

# Disable pwntools curses
ENV PWNLIB_NOTERM=1
# Minimal QT platform for angr-management
ENV QT_QPA_PLATFORM=minimal:enable_fonts

ADD scripts ./scripts
ADD conf ./conf
