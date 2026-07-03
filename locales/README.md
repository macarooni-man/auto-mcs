# Localization & Translation Guide

Welcome to the auto-mcs localization documentation! 

To maintain quality and avoid incomprehensible machine translations, **all translations are manually provided by the community**. If you are bilingual or notice incorrect translations in your native language, we highly encourage you to submit a Pull Request!

## How It Works Under The Hood

Instead of loading a massive single `locales.json` file into memory (which increases startup time and memory footprint), we split the translations into individual JSON files (e.g., `es.json`, `fr.json`).
- At runtime, the application **lazy-loads** only the language file requested by the user. 
- If the user uses English, no files are loaded at all. 

## Contributing Translations

1. Look in this `locales/` directory for the JSON file corresponding to your language (e.g. `es.json` for Spanish, `de.json` for German).
2. If you are adding a completely new language, simply create a new JSON file (e.g., `cn.json` for Chinese) using `en.json` as your template.
3. Open the JSON file and translate the values. **Do not modify the keys** (the strings on the left side of the colon).
4. **Placeholders:** You will often see `$$` inside the values. This represents a variable placeholder (like a server name or an IP address). Ensure that you keep `$$` in your translation exactly where the variable should appear in the translated sentence.
5. If a translation value is in English, it means it is a "fallback" and has not yet been translated. Feel free to translate it!

## For Developers: Adding New UI Strings

When you add new features or text to the auto-mcs UI (in the Python source code), you do **not** need to manually copy your new strings into all 10+ language files.

Instead, run the synchronization script:

```sh
python build-tools/locale_sync.py
```

**What this script does:**
1. Scans the Python codebase to extract all user-facing strings.
2. Formats and adds any new strings to `locales/en.json`.
3. Dynamically detects all other language files in the `locales/` directory.
4. Synchronizes the keys across every JSON file. If a key is missing in another language, it automatically inserts it with the English fallback text.
5. Sorts the keys alphabetically so Git diffs are clean and easy to review.

This guarantees that the app remains stable and never crashes due to missing keys, while allowing community translators to easily see what remains to be translated.
