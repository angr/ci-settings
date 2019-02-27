#!/sbin/suid
#!/bin/bash -ex -

BUILD_ID=$1
WORKER_ID=$2
BUILD_DEST="gs://${BUCKET}/${APP_NAME}-builds/${BUILD_ID}/testers/${WORKER_ID}"
ARTIFACTS="results/*"

if [ -f /conf/secret/google-cloud.json ]; then
    setup-creds.sh
    deactivate || true
    gsutil cp -a public-read -r $ARTIFACTS $BUILD_DEST
else
    echo 'Cannot upload build results - no private key. If you are doing this manually everything worked fine!'
fi
