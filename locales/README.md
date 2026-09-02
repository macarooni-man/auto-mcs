# Localization & Translation Guide

Welcome to the auto-mcs localization documentation!

The locale catalogs have an automatic DeepL baseline and are open to community
corrections. New UI text is translated automatically, while existing values
are never overwritten by the synchronization tool. If you are bilingual or
notice an incorrect translation, we highly encourage you to submit a Pull
Request!

## How It Works Under The Hood

Instead of loading a massive single `locales.json` file into memory (which increases startup time and memory footprint), we split the translations into individual JSON files (e.g., `es.json`, `fr.json`).
- At runtime, the application **lazy-loads** only the language file requested by the user. 
- If the user uses English, no files are loaded at all. 

## Contributing Translations

1. Look in this `locales/` directory for the JSON file corresponding to your language (e.g. `es.json` for Spanish, `de.json` for German).
2. If you are adding a completely new language, simply create a new JSON file (e.g., `cn.json` for Chinese) using `en.json` as your template.
3. Open the JSON file and translate the values. **Do not modify the keys** (the strings on the left side of the colon).
4. **Placeholders:** You will often see `$$` inside the values. This represents a variable placeholder (like a server name or an IP address). Ensure that you keep `$$` in your translation exactly where the variable should appear in the translated sentence.
5. Keep placeholders, commands, file paths, and keyboard shortcuts exactly as they appear. The synchronization tool protects these automatically for generated translations.

## For Developers: Adding New UI Strings

When you add new features or text to the auto-mcs UI (in the Python source code), you do **not** need to manually copy your new strings into all 10+ language files.

Set a DeepL API key in your environment (do not put it in a file or commit it):

```sh
export DEEPL_AUTH_KEY="your-key" # PowerShell: $env:DEEPL_AUTH_KEY = "your-key"
```

Then run the synchronization script:

```sh
python build-tools/locale_sync.py --translate
```

**What this script does:**
1. Scans the Python codebase to extract all user-facing strings.
2. Formats and adds any new strings to `locales/en.json`.
3. Dynamically detects all other language files in the `locales/` directory.
4. Uses DeepL to translate only keys that are absent from another language file. Existing community translations, including intentional empty values, are preserved.
5. Batches requests, protects placeholders, and writes every changed JSON file only after all DeepL requests succeed.
6. Sorts the keys alphabetically so Git diffs are clean and easy to review.

Review the generated translations before committing them. To validate the
catalogs without contacting DeepL or changing files, run:

```sh
python build-tools/locale_sync.py --check
```

`--check` is the command used in CI. It verifies that source strings exist in
`en.json` and that every active locale has every English key. It warns about
empty and obsolete entries without modifying them. Use `--translate --prune`
only when you intentionally want to remove obsolete keys.

DeepL Free keys end in `:fx` and are detected automatically; other keys use
the Pro endpoint. The API key is never needed by auto-mcs at runtime and is
never included in packaged builds.
