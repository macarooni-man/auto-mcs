/*
 * Android Java command-line launcher for auto-mcs.
 * The APK installs this executable under nativeLibraryDir as libautomcsjava<V>.so.
 * It is a PIE executable, not a JNI library: subprocess.Popen can exec it directly.
 * The executable name selects the Java runtime in AUTO_MCS_JAVA_ROOT.
 */
#include <dlfcn.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef int (*jli_launch)(int, char **, int, const char **, int, const char **,
                          const char *, const char *, const char *, const char *,
                          unsigned char, unsigned char, unsigned char, int);

static int exists(const char *path) {
    return access(path, R_OK) == 0;
}

static void append_path(char *dst, size_t size, const char *part) {
    if (!part || !*part) return;
    if (*dst) strncat(dst, ":", size - strlen(dst) - 1);
    strncat(dst, part, size - strlen(dst) - 1);
}

static const char *find_lib(const char *home, const char *name, char *output, size_t length) {
    const char *dirs[] = {"lib", "lib/jli", "lib/server", "lib/aarch64",
                          "lib/aarch64/jli", "lib/aarch64/server",
                          "jre/lib/aarch64", "jre/lib/aarch64/jli",
                          "jre/lib/aarch64/server", NULL};
    for (int i = 0; dirs[i]; ++i) {
        if (snprintf(output, length, "%s/%s/%s", home, dirs[i], name) >= (int)length) continue;
        if (exists(output)) return output;
    }
    return NULL;
}

static void load_if_present(const char *home, const char *name) {
    char path[PATH_MAX];
    if (find_lib(home, name, path, sizeof(path))) {
        void *handle = dlopen(path, RTLD_NOW | RTLD_GLOBAL);
        if (!handle) fprintf(stderr, "[Android Java] %s: %s\n", name, dlerror());
    }
}

int main(int argc, char **argv) {
    const char *name = strrchr(argv[0], '/');
    name = name ? name + 1 : argv[0];

    int version = 0;
    if (sscanf(name, "libautomcsjava%d.so", &version) != 1 ||
            (version != 8 && version != 17 && version != 21 && version != 25)) {
        fprintf(stderr, "[Android Java] Unsupported launcher name: %s\n", name);
        return 2;
    }

    const char *root = getenv("AUTO_MCS_JAVA_ROOT");
    if (!root || !*root) {
        fprintf(stderr, "[Android Java] AUTO_MCS_JAVA_ROOT is not set\n");
        return 2;
    }

    char home[PATH_MAX];
    if (snprintf(home, sizeof(home), "%s/android-java%d", root, version) >= (int)sizeof(home)) return 2;
    char path[PATH_MAX], libraries[8192] = "";
    char vm_path[PATH_MAX];
    if (!find_lib(home, "libjvm.so", vm_path, sizeof(vm_path))) {
        fprintf(stderr, "[Android Java] Missing libjvm.so under %s\n", home);
        return 2;
    }
    char *vm_file = strrchr(vm_path, '/');
    if (!vm_file) return 2;
    *vm_file = '\0';

    /* libjli requires the JVM library directory to be FIRST. Otherwise it
     * attempts to re-exec JAVA_HOME/bin/java, which Android blocks. */
    append_path(libraries, sizeof(libraries), vm_path);
    const char *dirs[] = {"lib/jli", "lib/server", "lib", "lib/aarch64/jli",
                          "lib/aarch64/server", "lib/aarch64",
                          "jre/lib/aarch64/jli", "jre/lib/aarch64/server",
                          "jre/lib/aarch64", NULL};
    for (int i = 0; dirs[i]; ++i) {
        if (snprintf(path, sizeof(path), "%s/%s", home, dirs[i]) < (int)sizeof(path))
            append_path(libraries, sizeof(libraries), path);
    }

    const char *old_path = getenv("LD_LIBRARY_PATH");
    append_path(libraries, sizeof(libraries), old_path);
    setenv("LD_LIBRARY_PATH", libraries, 1);
    setenv("JAVA_HOME", home, 1);
    setenv("JDK_JAVA_OPTIONS", "", 1);
    setenv("_JAVA_OPTIONS", "", 1);
    if (!getenv("TMPDIR")) setenv("TMPDIR", "/data/local/tmp", 0);

    char jli_path[PATH_MAX];
    if (!find_lib(home, "libjli.so", jli_path, sizeof(jli_path))) {
        fprintf(stderr, "[Android Java] Missing libjli.so under %s\n", home);
        return 2;
    }

    /* Match Pojav/Amethyst: libjli must be loaded before libjvm. */
    void *jli = dlopen(jli_path, RTLD_NOW | RTLD_GLOBAL);
    if (!jli) {
        fprintf(stderr, "[Android Java] Failed to load %s: %s\n", jli_path, dlerror());
        return 127;
    }

    load_if_present(home, "libjvm.so");
    load_if_present(home, "libverify.so");
    load_if_present(home, "libjava.so");
    load_if_present(home, "libnet.so");
    load_if_present(home, "libnio.so");
    load_if_present(home, "libzip.so");

    jli_launch launch = (jli_launch)dlsym(jli, "JLI_Launch");
    if (!launch) {
        fprintf(stderr, "[Android Java] JLI_Launch not exported: %s\n", dlerror());
        return 127;
    }

    return launch(argc, argv, 0, NULL, 0, NULL,
                  "1.8.0-internal", "1.8", "java", "java", 0, 1, 0, 0);
}
