#!/bin/bash

cd
if [ -z "$GOAHEAD" ]; then
    git -C ci-settings fetch
    git -C ci-settings reset --hard origin/${BRANCH_NAME-master}
    export GOAHEAD=1
    exec $0 "$@"
fi

git clone https://github.com/angr/wheels || true
git -C wheels fetch
git -C wheels reset --hard origin/${BRANCH_NAME-master}

sudo apt update
sudo apt upgrade -y
sudo apt install -y vim build-essential python3 python3-dev python3-pip python3-setuptools zip git libffi-dev libtool libtool-bin wget automake bison cmake nasm clang libglib2.0-dev socat libc6:i386 libgcc1:i386 libstdc++6:i386 libtinfo5:i386 zlib1g:i386
sudo -H pip3 install virtualenv pygithub
echo "hello friends"
