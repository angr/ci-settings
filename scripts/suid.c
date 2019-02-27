#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    // argv[1] = target binary
    // argv[2:] = target arguments
    // we want to execute /bin/bash -ex - [target] [arguments]

    setuid(0);
    //uid_t r, e, s;
    //getresuid(&r, &e, &s);
    //printf("r = %u e = %u s = %u\n", r, e, s);

    if (argc < 2) {
        puts("Bad usage");
        return 1;
    }

    if (strcmp(argv[1], "/bin/publish-build.sh") == 0 ||
        strcmp(argv[1], "/bin/download-build.sh") == 0 ||
        strcmp(argv[1], "/bin/publish-results.sh") == 0) {

    } else {
        puts("Bad target");
        return 1;
    }

    char *env_whitelist[] = {"BUCKET", "APP_NAME"};

    char **newenv = calloc(sizeof(env_whitelist) / sizeof(char*) + 2, sizeof(char*));
    char **newargv = calloc(argc + 3, sizeof(char*));

    newenv[0] = "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/utils/gsutil";

    for (size_t i_src = 0, i_dst = 1; i_src < sizeof(env_whitelist) / sizeof(char*); i_src++) {
        char *val = getenv(env_whitelist[i_src]);
        if (val) {
            newenv[i_dst] = malloc(strlen(val) + strlen(env_whitelist[i_src]) + 2);
            sprintf(newenv[i_dst], "%s=%s", env_whitelist[i_src], val);
            i_dst++;
        }
    }

    newargv[0] = "/bin/bash";
    newargv[1] = "-ex";
    newargv[2] = "-";
    memcpy(&newargv[3], &argv[1], (argc - 1) * sizeof(char*));
    execve("/bin/bash", newargv, newenv);

    puts("Could not execute");
    return 1;
}
