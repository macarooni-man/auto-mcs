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
    bootstrap = root / "pythonforandroid" / "bootstraps" / "common" / "build" / "jni" / "application" / "src" / "start.c"

    if not recipe.is_file():
        fail(f"Missing Python recipe: '{recipe}'")

    if not bootstrap.is_file():
        fail(f"Missing Python bootstrap: '{bootstrap}'")

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
        bootstrap,
        """      PyConfig config;
      PyConfig_InitPythonConfig(&config);
      config.program_name = L"android_python";
""",
        """      PyConfig config;
      PyConfig_InitPythonConfig(&config);

      // PythonActivity sets PYTHONHOME/PYTHONPATH to the app root, but p4a's
      // actual stdlib lives in _python_bundle. Python 3.12 must use the
      // explicit module_search_paths below instead of interpreting those
      // environment variables as a normal CPython installation.
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
