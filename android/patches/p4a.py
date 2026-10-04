from pathlib import Path
import sys


def fail(message):
    raise RuntimeError(f"[android p4a patch] {message}")


def replace_once(path, old, new, description):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    count = text.count(old)

    if count != 1:
        fail(f"{description}: expected exactly one anchor in '{path}', found {count}")

    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[android p4a patch] {description}")


def main():
    if len(sys.argv) != 2:
        fail("Usage: p4a.py <python-for-android-root>")

    root = Path(sys.argv[1]).resolve()

    recipe = root / "pythonforandroid" / "recipes" / "python3" / "__init__.py"
    rust_recipe = root / "pythonforandroid" / "recipe.py"
    bootstrap = root / "pythonforandroid" / "bootstraps" / "common" / "build" / "jni" / "application" / "src" / "start.c"
    activity = root / "pythonforandroid" / "bootstraps" / "sdl2" / "build" / "src" / "main" / "java" / "org" / "kivy" / "android" / "PythonActivity.java"
    python_patch = root / "pythonforandroid" / "recipes" / "python3" / "patches" / "auto_mcs_android_libpython.patch"

    if not recipe.is_file():
        fail(f"Missing Python recipe: '{recipe}'")

    if not rust_recipe.is_file():
        fail(f"Missing p4a recipe module: '{rust_recipe}'")

    if not bootstrap.is_file():
        fail(f"Missing Python bootstrap: '{bootstrap}'")

    if not activity.is_file():
        fail(f"Missing PythonActivity: '{activity}'")


    # ----------------------------------------------- Android Back ------------------------------------------------------

    replace_once(
        activity,
        """import android.os.AsyncTask;
""",
        """import android.os.AsyncTask;
import android.os.Build;
""",
        "imported Android API version support",
    )

    replace_once(
        activity,
        """import android.util.Log;
""",
        """import android.util.Log;
import android.view.KeyEvent;
""",
        "imported Android key event support",
    )

    replace_once(
        activity,
        """import android.view.ViewGroup;
""",
        """import android.view.ViewGroup;
import android.window.OnBackInvokedCallback;
import android.window.OnBackInvokedDispatcher;
""",
        "imported Android back navigation interfaces",
    )

    replace_once(
        activity,
        """    public String getAppRoot() {
        String app_root = getFilesDir().getAbsolutePath() + "/app";
        return app_root;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
""",
        """    public String getAppRoot() {
        String app_root = getFilesDir().getAbsolutePath() + "/app";
        return app_root;
    }

    private void dispatchEscape() {
        SDLActivity.onNativeKeyDown(KeyEvent.KEYCODE_ESCAPE);
        SDLActivity.onNativeKeyUp(KeyEvent.KEYCODE_ESCAPE);
    }

    private static class BackHandlerApi33 {
        static void register(final PythonActivity activity) {
            activity.getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                    new OnBackInvokedCallback() {
                        @Override
                        public void onBackInvoked() {
                            activity.dispatchEscape();
                        }
                    });
        }
    }

    @SuppressWarnings("deprecation")
    @Override
    public void onBackPressed() {
        if (Build.VERSION.SDK_INT < 33) {
            dispatchEscape();
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
""",
        "routed Android back navigation through SDL escape",
    )

    replace_once(
        activity,
        """        super.onCreate(savedInstanceState);
        Log.v(TAG, "Did super onCreate");

        this.mActivity = this;
""",
        """        super.onCreate(savedInstanceState);
        Log.v(TAG, "Did super onCreate");

        if (Build.VERSION.SDK_INT >= 33) {
            BackHandlerApi33.register(this);
        }

        this.mActivity = this;
""",
        "registered Android back navigation callback",
    )


    # ----------------------------------------------- CPython ----------------------------------------------------------

    python_patch.write_text(
        """diff --git a/Makefile.pre.in b/Makefile.pre.in
--- a/Makefile.pre.in
+++ b/Makefile.pre.in
@@ -2802,7 +2802,7 @@ Python/thread.o: @THREADHEADERS@ $(srcdir)/Python/condvar.h

 # force rebuild when header file or module build flavor (static/shared) is changed
 MODULE_DEPS_STATIC=Modules/config.c
-MODULE_DEPS_SHARED=$(MODULE_DEPS_STATIC) $(EXPORTSYMS)
+MODULE_DEPS_SHARED=$(MODULE_DEPS_STATIC) $(EXPORTSYMS) $(LDLIBRARY)

 MODULE_CMATH_DEPS=$(srcdir)/Modules/_math.h
 MODULE_MATH_DEPS=$(srcdir)/Modules/_math.h
diff --git a/Modules/makesetup b/Modules/makesetup
--- a/Modules/makesetup
+++ b/Modules/makesetup
@@ -286,7 +286,7 @@ do
 				esac
 			esac
 			rule="$file: $objs"
-			rule="$rule; \\$(BLDSHARED) $objs $libs $ExtraLibs -o $file"
+			rule="$rule; \\$(BLDSHARED) $objs $libs $ExtraLibs \\$(BLDLIBRARY) -o $file"
 			echo "$rule" >>$rulesf
 		done
 	done
""",
        encoding="utf-8",
    )

    replace_once(
        recipe,
        """    patches = [
        'patches/pyconfig_detection.patch',
        'patches/reproducible-buildinfo.diff',
    ]
""",
        """    patches = [
        'patches/pyconfig_detection.patch',
        'patches/reproducible-buildinfo.diff',
        'patches/auto_mcs_android_libpython.patch',
    ]
""",
        "backported CPython Android libpython extension linking",
    )

    replace_once(
        rust_recipe,
        """        env["RUSTFLAGS"] = "-Clink-args=-L{} -L{}".format(
            self.ctx.get_libs_dir(arch.arch), join(realpython_dir, "android-build")
        )
""",
        """        env["RUSTFLAGS"] = "-Clink-args=-L{} -L{} -lpython{}".format(
            self.ctx.get_libs_dir(arch.arch), join(realpython_dir, "android-build"),
            self.python_major_minor_version
        )
""",
        "linked Rust Python extensions against libpython",
    )

    replace_once(
        recipe,
        """        'ac_cv_header_bzlib_h=no',
    ]
""",
        """        'ac_cv_header_bzlib_h=no',

        # CPython 3.12 incorrectly enables grp while cross-compiling for
        # Android even though Bionic does not provide getgrent/setgrent/endgrent.
        'ac_cv_func_getgrgid=no',
        'ac_cv_func_getgrgid_r=no',
    ]
""",
        "disabled CPython grp module for Android",
    )

    replace_once(
        recipe,
        """        env['LDFLAGS'] = env.get('LDFLAGS', '')
        if shutil.which('lld') is not None:
""",
        """        env['LDFLAGS'] = env.get('LDFLAGS', '')

        # Android API 23+ loads shared libraries locally by default. CPython
        # 3.12 extension modules reference Python API symbols from libpython,
        # so mark libpython DF_1_GLOBAL at link time to make those symbols
        # visible to modules loaded later with dlopen().
        env['BLDSHARED'] = f"{env['CC']} -shared -Wl,-z,global"

        if shutil.which('lld') is not None:
""",
        "marked libpython as globally visible to Android extensions",
    )

    replace_once(
        recipe,
        """            info("Zip {} files into the bundle".format(len(stdlib_filens)))
            shprint(sh.zip, '-X', stdlib_zip, *stdlib_filens)
""",
        """            info("Zip {} files into the bundle".format(len(stdlib_filens)))

            # CPython needs encodings while initializing the filesystem codec,
            # before native extension modules such as zlib are guaranteed to
            # be importable. Store encodings uncompressed so zipimport can
            # bootstrap without requiring zlib first.
            encoding_filens = [filen for filen in stdlib_filens if filen.startswith('./encodings/')]
            remaining_filens = [filen for filen in stdlib_filens if filen not in encoding_filens]

            shprint(sh.zip, '-0', '-X', stdlib_zip, *encoding_filens)
            shprint(sh.zip, '-X', stdlib_zip, *remaining_filens)
""",
        "stored bootstrap encodings without compression",
    )

    replace_once(
        bootstrap,
        """      PyConfig config;
      PyConfig_InitPythonConfig(&config);
      config.program_name = L"android_python";
""",
        """      PyConfig config;
      PyConfig_InitPythonConfig(&config);

      // PythonActivity sets PYTHONHOME/PYTHONPATH to the app root, but p4a's
      // actual stdlib lives in _python_bundle. Use the explicit module search
      // paths below instead of interpreting those variables as a normal
      // CPython installation.
      config.use_environment = 0;
      config.user_site_directory = 0;
      config.optimization_level = 2;

      PyStatus config_status = PyConfig_SetString(
          &config, &config.program_name, L"android_python");
      if (PyStatus_Exception(config_status)) {
          LOGP("Failed to configure Python program name:");
          LOGP(config_status.err_msg ? config_status.err_msg : "unknown error");
          PyConfig_Clear(&config);
          return -1;
      }
""",
        "isolated Python bootstrap from Android PYTHONHOME/PYTHONPATH",
    )

    replace_once(
        bootstrap,
        """    PyStatus status = Py_InitializeFromConfig(&config);
    if (PyStatus_Exception(status)) {
        LOGP("Python initialization failed:");
        LOGP(status.err_msg);
    }
""",
        """    PyStatus status = Py_InitializeFromConfig(&config);
    if (PyStatus_Exception(status)) {
        LOGP("Python initialization failed:");
        LOGP(status.err_msg ? status.err_msg : "unknown error");
        PyConfig_Clear(&config);
        return -1;
    }
    PyConfig_Clear(&config);
""",
        "made Python initialization failure fatal and deterministic",
    )


if __name__ == "__main__":
    main()
