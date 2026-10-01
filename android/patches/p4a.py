from pathlib import Path
import sys


def fail(message):
    raise RuntimeError(f"[android p4a patch] {message}")


def main():
    if len(sys.argv) != 2:
        fail("Usage: p4a.py <python-for-android-root>")

    root = Path(sys.argv[1]).resolve()
    recipe = root / "pythonforandroid" / "recipes" / "python3" / "__init__.py"

    if not recipe.is_file():
        fail(f"Missing Python recipe: '{recipe}'")

    text = recipe.read_text(encoding="utf-8")

    old = """        'ac_cv_header_bzlib_h=no',
    ]
"""

    new = """        'ac_cv_header_bzlib_h=no',

        # CPython 3.12 incorrectly enables grp while cross-compiling for
        # Android even though Bionic does not provide getgrent/setgrent/endgrent.
        # auto-mcs does not use grp, so disable it explicitly.
        'ac_cv_func_getgrgid=no',
        'ac_cv_func_getgrgid_r=no',
    ]
"""

    if new in text:
        print("[android p4a patch] CPython Android grp workaround already applied")
        return

    count = text.count(old)
    if count != 1:
        fail(f"Expected one Python configure anchor, found {count}")

    recipe.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("[android p4a patch] Disabled CPython grp module for Android")


if __name__ == "__main__":
    main()
