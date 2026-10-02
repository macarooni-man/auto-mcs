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
        "#define P4A_MIN_VER 11",
        """// Keep Python 3.12 on p4a's legacy initialization path.
// Py_SetPath/Py_Initialize is still supported by CPython 3.12 and is the
// bootstrap path used by the older auto-mcs Android build.
#define P4A_MIN_VER 13""",
        "restored legacy Python bootstrap for Python 3.12",
    )


if __name__ == "__main__":
    main()
