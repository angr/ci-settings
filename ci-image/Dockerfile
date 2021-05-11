FROM ubuntu:bionic
USER root
WORKDIR /root
RUN chmod 755 .

# install deps. make sure not to create too-large layers
RUN dpkg --add-architecture i386
RUN apt-get update
RUN apt-get install -y vim build-essential python3 python3-dev python3-pip python3-setuptools zip git libffi-dev libtool libtool-bin wget automake bison cmake nasm clang socat lld
RUN apt-get install -y libglib2.0-dev libc6:i386 libgcc1:i386 libstdc++6:i386 libtinfo5:i386 zlib1g:i386
RUN apt-get install -y libc6-armhf-cross libc6-arm64-cross libc6-mips-cross libc6-mips64-cross libc6-powerpc-cross libc6-powerpc-ppc64-cross
RUN apt-get install -y gdb gdbserver gdb-multiarch openjdk-8-jdk-headless docker.io libgl1
RUN apt-get install -y binutils-mips-linux-gnu binutils-mipsel-linux-gnu binutils-arm-linux-gnueabi
RUN apt-get install -y strace
RUN pip3 install "virtualenv<20" pygithub

# This command is used to fix problems with libc6-cross packages
# this is only a temporary solution and should be fixed in the ubuntu packages in the future
# more detail can be found at angr/ci-settings#11 and bugs.launchpad.net/qemu/+bug/1701798
RUN mkdir /usr/mips-linux-gnu/etc /usr/mips64-linux-gnuabi64/etc /usr/powerpc-linux-gnu/etc /usr/powerpc64-linux-gnu/etc \
    && ln -s /dev/null /usr/mips-linux-gnu/etc/ld.so.cache \
    && ln -s /dev/null /usr/mips64-linux-gnuabi64/etc/ld.so.cache \
    && ln -s /dev/null /usr/powerpc-linux-gnu/etc/ld.so.cache \
    && ln -s /dev/null /usr/powerpc64-linux-gnu/etc/ld.so.cache

RUN umask 0; git clone https://github.com/angr/wheels.git
ADD scripts ./scripts
ADD conf ./conf
ENTRYPOINT ["/root/scripts/entrypoint.sh"]
