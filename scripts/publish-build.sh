#!/sbin/suid
#!/bin/bash -ex -

BUILD_ID=$1
BUILD_DEST="gs://${BUCKET}/${APP_NAME}-builds/${BUILD_ID}"
BUILD_FILES="src virtualenv tests.txt"
BUILD_ARCHIVE="build.tar.gz"
ARTIFACTS="$BUILD_ARCHIVE install.sh requirements.txt freeze.txt tests.txt"

if [ -f /conf/secret/google-cloud.json ]; then
    tar -czf $BUILD_ARCHIVE $BUILD_FILES
    setup-creds.sh
    deactivate || true
    gsutil cp -a public-read $ARTIFACTS $BUILD_DEST
else
    echo 'Cannot upload build slug - no private key. If you are doing this manually everything worked fine!'
fi
