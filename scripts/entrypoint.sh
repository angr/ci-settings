#!/bin/bash
chmod 777 .

# DO NOT CHANGE THIS TO exec su
# this will mean that su is pid 1
# su will kill itself if it ever gets a SIGCHLD for any reason
# DON'T MAKE THE SAME MISTAKE I DID AND WASTE 3 DAYS DEBUGGING THIS
su user -c "$*"

echo "FINAL EXIT STATUS: $?"
