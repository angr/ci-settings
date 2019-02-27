#!/sbin/suid
#!/bin/bash -ex -

BUILD_ID=$1
if [ -f /conf/secret/google-cloud.json ]; then
    setup-creds.sh || true
    deactivate || true
    gsutil cp "gs://${BUCKET}/${APP_NAME}-builds/${BUILD_ID}/build.tar.gz" - | tar -xz
    gsutil cp "gs://${BUCKET}/${APP_NAME}-builds/${BUILD_ID}/timeinfo.json" timeinfo.json
else
    wget "https://storage.googleapis.com/${BUCKET}/${APP_NAME}-builds/${BUILD_ID}/build.tar.gz" -O - --progress=dot:giga | tar -xz
fi
