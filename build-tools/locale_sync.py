"""Synchronize auto-mcs locale catalogs and translate new entries with DeepL.

The application only reads locale files at runtime. This tool is intentionally
the sole place where automatic translation happens so API credentials never
need to be bundled with auto-mcs.
"""

from __future__ import annotations

import argparse
import ast
import copy
import html
import json
import os
import re
import sys
import tempfile
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEEPL_FREE_ENDPOINT = "https://api-free.deepl.com"
DEEPL_PRO_ENDPOINT = "https://api.deepl.com"
DEEPL_AUTH_KEY_ENV = "DEEPL_AUTH_KEY"
MAX_REQUEST_BYTES = 120 * 1024
MAX_RETRIES = 3

# The filenames are the application's locale codes. DeepL has more specific
# target-language codes for Portuguese and English variants.
LOCALE_TARGETS = {
    "de": "DE",
    "e2": "EN-US",  # The existing "English 2" pseudo-locale.
    "es": "ES",
    "fi": "FI",
    "fr": "FR",
    "it": "IT",
    "nl": "NL",
    "pt": "PT-PT",
    "sv": "SV",
}

DEEPL_CONTEXT = (
    "auto-mcs is a cross-platform graphical application for managing Minecraft "
    "servers. Preserve product names such as auto-mcs, Minecraft, Java, "
    "Modrinth, Telepath, and playit.gg. Preserve commands, file paths, keyboard "
    "shortcuts, and placeholders exactly."
)

# auto-mcs uses $$ and $name$ placeholders at runtime. Protect common Python
# formatting forms as well, so new UI code cannot have interpolation broken by
# a translation service.
PLACEHOLDER_RE = re.compile(
    r"\$\$|\$[^$\n]+\$|%\([^)]+\)[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z]|"
    r"%[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z]|\{\{[^{}]+\}\}|\{[^{}]+\}|"
    r"(?i:\b(?:ctrl|alt|shift|cmd|command|option|win)(?:[+-](?:ctrl|alt|shift|cmd|command|option|win|[a-z0-9]))+\b)|"
    r"\[/?[a-zA-Z][^\]]*\]"
)
PROTECTED_TAG_RE = re.compile(
    r'<x\s+id="(\d+)"\s*/\s*>|<x\s+id="(\d+)"\s*>\s*</x\s*>', re.IGNORECASE
)


class LocaleSyncError(RuntimeError):
    """A safe, user-facing failure while preparing locale updates."""


class DeepLAPIError(LocaleSyncError):
    """A DeepL response prevented the locale transaction from completing."""


def project_paths() -> tuple[Path, Path]:
    current_dir = Path(__file__).resolve().parent
    return current_dir.parent / "source", current_dir.parent / "locales"


def format_locale_json(data: dict[str, str]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True) + "\n"


def load_locale(path: Path) -> dict[str, str]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise LocaleSyncError(f"Unable to read {path}: {error}") from error

    if not isinstance(data, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in data.items()
    ):
        raise LocaleSyncError(f"{path} must contain a JSON object with string keys and values.")
    return data


def discover_locales(locales_dir: Path) -> dict[str, Path]:
    paths = {path.stem: path for path in sorted(locales_dir.glob("*.json"))}
    if "en" not in paths:
        raise LocaleSyncError(f"Missing English source catalog: {locales_dir / 'en.json'}")
    return paths


def source_terms(source_dir: Path) -> list[str]:
    """Extract terms using the legacy sync rules so existing catalogs stay stable."""
    all_terms: list[str] = []
    skip_basenames = {
        "desktop.py", "logviewer.py", "amseditor.py",
        "backup.py", "acl.py", "constants.py", "init.py",
        "launcher.py", "addons.py", "amscript.py", "foundry.py",
        "java.py", "playit.py", "audio.py", "logger.py",
    }
    skip_dirs = {".git", "__pycache__", ".venv", "venv", "env", "build", "dist", "headless"}

    py_files = sorted(
        path for path in source_dir.rglob("*.py")
        if path.name not in skip_basenames and not any(part in skip_dirs for part in path.parts)
    )

    for script in py_files:
        try:
            tree = ast.parse(script.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, SyntaxError) as error:
            raise LocaleSyncError(f"Unable to parse {script}: {error}") from error

        last_line = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            string = node.value

            lineno = getattr(node, "lineno", 0)
            basename = script.name
            if basename == "constants.py" and (
                lineno < 4400 and lineno not in range(550, 600) and lineno not in range(1900, 2100)
            ):
                continue
            if basename == "amseditor.py" and lineno < 880:
                continue
            if "-XX:+UseG1GC" in string or "xbox-achievements-enabled: true" in string:
                continue
            if "namespace eval tabdrag" in string or re.match(r"^\<.*\>$", string) or re.match(r"[A-Z][a-z]+\.[A-Z][a-z]+", string):
                continue

            if "$" not in string:
                if re.search(r"^(http|\!|\#|\.|\&|\-|\[\^|\[\/|\/|\\|\*|\@)", string) or re.search(r"(\.txt|\.png|\.json|\.ini)$", string):
                    continue
                if string.count("%") > 2 or string in {"macos", "linux", "windows", "user32", "utf-8", "uuid"}:
                    continue
                if "_" in string and " " not in string:
                    continue
                if "[color=" in string or "[/color]" in string or ".*" in string or "- Internal use only" in string:
                    continue
                if re.search(r"v?\d+(\.?\d+)+\w?", string) and " " not in string:
                    continue
                spaces = re.findall(r"\s+", string)
                if spaces and len(max(spaces, key=len)) > 5:
                    continue
                if "Manager: " in string:
                    string = string.split(":", 1)[0]

            if "\ngenerate-structures=true\nspawn-animals=true\nsnooper-enabled=true\n" in string:
                continue
            if re.match(r"^\w+Screen$", string) or not string.strip() or not re.sub(r"[^a-zA-Z0-9$]", "", string):
                continue

            partial_matches = ("'$", "$'", "$$", '$)')
            if string.count("$") < 2 and string.strip() != "$" and string.strip() not in partial_matches:
                if len(re.sub(r"[a-zA-Z0-9 ]", "", string)) > len(re.sub(r"[^a-zA-Z0-9 ]", "", string)):
                    continue

            if string not in all_terms or "$" in string:
                if "$" in string and lineno == last_line and all_terms and "$" in all_terms[-1]:
                    all_terms[-1] += string
                else:
                    all_terms.append(string)
            last_line = lineno

    return all_terms


def canonical_entry(string: str) -> tuple[str, str]:
    if string.count("$") == 1:
        string = string.replace("$", "$$")
    if "'$$" in string and "'$$'" not in string:
        string = string.replace("'$$", "'$$'")
    if "$$'" in string and "'$$'" not in string:
        string = string.replace("$$'", "'$$'")

    key = string.lower().strip()
    if "$" in key:
        key = re.sub(r"\$[^$]*\$", "$$", key)
    return key, "understood" if key == "okay" else string


def update_english_catalog(
    existing: dict[str, str], terms: Iterable[str]
) -> tuple[dict[str, str], set[str]]:
    extracted = dict(canonical_entry(term) for term in terms)
    catalog = dict(existing)
    added = set(extracted) - set(existing)
    for key, value in extracted.items():
        catalog.setdefault(key, value)
    return catalog, added


def validate_catalogs(
    expected_keys: set[str], english: dict[str, str], locales: dict[str, dict[str, str]]
) -> dict[str, Any]:
    missing_english = expected_keys - set(english)
    missing_by_locale = {code: set(english) - set(data) for code, data in locales.items()}
    orphaned_by_locale = {code: set(data) - set(english) for code, data in locales.items()}
    empty_by_locale = {
        code: {key for key, value in data.items() if not value.strip()}
        for code, data in locales.items()
    }
    return {
        "missing_english": missing_english,
        "missing_by_locale": missing_by_locale,
        "orphaned_by_locale": orphaned_by_locale,
        "empty_by_locale": empty_by_locale,
    }


def shield_placeholders(text: str) -> tuple[str, list[str]]:
    """Encode literal text as XML and replace protected fragments with XML tags."""
    tokens: list[str] = []
    parts: list[str] = []
    position = 0
    for match in PLACEHOLDER_RE.finditer(text):
        parts.append(html.escape(text[position:match.start()], quote=False))
        tokens.append(match.group(0))
        parts.append(f'<x id="{len(tokens) - 1}"/>')
        position = match.end()
    parts.append(html.escape(text[position:], quote=False))
    return "".join(parts), tokens


def restore_placeholders(text: str, tokens: list[str]) -> str:
    identifiers: list[int] = []

    def replace(match: re.Match[str]) -> str:
        identifier = int(match.group(1) or match.group(2))
        identifiers.append(identifier)
        if identifier >= len(tokens):
            raise DeepLAPIError("DeepL returned an unknown protected placeholder.")
        return tokens[identifier]

    restored = PROTECTED_TAG_RE.sub(replace, text)
    if identifiers != list(range(len(tokens))):
        raise DeepLAPIError("DeepL changed, removed, or duplicated a protected placeholder.")
    return html.unescape(restored)


def translation_payload(texts: list[str], target_language: str) -> dict[str, Any]:
    return {
        "text": texts,
        "source_lang": "EN",
        "target_lang": target_language,
        "context": DEEPL_CONTEXT,
        "model_type": "prefer_quality_optimized",
        "tag_handling": "xml",
        "ignore_tags": ["x"],
        "split_sentences": "nonewlines",
    }


def batch_texts(
    texts: list[str], target_language: str, maximum_bytes: int = MAX_REQUEST_BYTES
) -> list[list[str]]:
    """Batch encoded texts while leaving room below DeepL's 128 KiB limit."""
    batches: list[list[str]] = []
    current: list[str] = []
    for text in texts:
        candidate = current + [text]
        size = len(
            json.dumps(
                translation_payload(candidate, target_language),
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        if size > maximum_bytes:
            if not current:
                raise DeepLAPIError("A single UI string exceeds DeepL's request-size limit.")
            batches.append(current)
            single_size = len(
                json.dumps(
                    translation_payload([text], target_language),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            if single_size > maximum_bytes:
                raise DeepLAPIError("A single UI string exceeds DeepL's request-size limit.")
            current = [text]
        else:
            current = candidate
    if current:
        batches.append(current)
    return batches


def deepl_endpoint(auth_key: str) -> str:
    return DEEPL_FREE_ENDPOINT if auth_key.strip().endswith(":fx") else DEEPL_PRO_ENDPOINT


def translation_response(data: Any, expected_count: int) -> list[str]:
    if not isinstance(data, dict) or not isinstance(data.get("translations"), list):
        raise DeepLAPIError("DeepL returned an invalid translation response.")
    translations = data["translations"]
    if len(translations) != expected_count or not all(
        isinstance(item, dict) and isinstance(item.get("text"), str) for item in translations
    ):
        raise DeepLAPIError("DeepL returned an incomplete translation response.")
    return [item["text"] for item in translations]


class DeepLClient:
    def __init__(
        self,
        auth_key: str,
        opener: Callable[..., Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        if not auth_key.strip():
            raise DeepLAPIError(f"Set {DEEPL_AUTH_KEY_ENV} before translating missing locale strings.")
        self.auth_key = auth_key.strip()
        self.endpoint = deepl_endpoint(self.auth_key)
        self.opener = opener
        self.sleeper = sleeper

    def _request_json(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        body = (
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            if payload is not None
            else None
        )
        request = Request(
            f"{self.endpoint}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"DeepL-Auth-Key {self.auth_key}",
                "Content-Type": "application/json",
                "User-Agent": "auto-mcs-locale-sync/1.0",
            },
        )

        for attempt in range(MAX_RETRIES + 1):
            try:
                with self.opener(request, timeout=30) as response:
                    raw = response.read().decode("utf-8")
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise DeepLAPIError("DeepL returned a non-object JSON response.")
                return result
            except HTTPError as error:
                retryable = error.code == 429 or 500 <= error.code < 600
                retry_after = error.headers.get("Retry-After") if error.headers else None
                error.close()
                if error.code == 456:
                    raise DeepLAPIError("DeepL quota is exhausted; locale files were not changed.") from error
                if not retryable or attempt == MAX_RETRIES:
                    raise DeepLAPIError(f"DeepL request failed with HTTP {error.code}.") from error
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
            except (URLError, TimeoutError) as error:
                if attempt == MAX_RETRIES:
                    raise DeepLAPIError(f"Unable to reach DeepL: {error}") from error
                delay = 2 ** attempt
            except json.JSONDecodeError as error:
                raise DeepLAPIError("DeepL returned invalid JSON.") from error
            self.sleeper(delay)

        raise AssertionError("DeepL retry loop unexpectedly completed")

    def usage(self) -> tuple[int, int]:
        data = self._request_json("GET", "/v2/usage")
        count, limit = data.get("character_count"), data.get("character_limit")
        if not isinstance(count, int) or not isinstance(limit, int):
            raise DeepLAPIError("DeepL usage response did not include character limits.")
        return count, limit

    def ensure_quota(self, required_characters: int) -> None:
        used, limit = self.usage()
        if required_characters > limit - used:
            raise DeepLAPIError(
                f"DeepL has {limit - used:,} characters remaining, but {required_characters:,} are required; locale files were not changed."
            )

    def translate_many(self, target_language: str, texts: list[str]) -> dict[str, str]:
        unique_texts = list(dict.fromkeys(texts))
        protected = {text: shield_placeholders(text) for text in unique_texts}
        protected_to_sources: dict[str, list[str]] = {}
        for source, (protected_text, _) in protected.items():
            protected_to_sources.setdefault(protected_text, []).append(source)
        translated: dict[str, str] = {}
        for batch in batch_texts([protected[text][0] for text in unique_texts], target_language):
            response = self._request_json("POST", "/v2/translate", translation_payload(batch, target_language))
            translated_values = translation_response(response, len(batch))
            for protected_text, translated_text in zip(batch, translated_values, strict=True):
                original = protected_to_sources[protected_text].pop(0)
                translated[original] = restore_placeholders(translated_text, protected[original][1])
        return translated


def locale_candidates(
    english: dict[str, str],
    locales: dict[str, dict[str, str]],
    client: DeepLClient | Any | None,
    prune: bool,
) -> tuple[dict[str, dict[str, str]], dict[str, set[str]]]:
    """Return changed copies only after every required translation has succeeded."""
    candidates = copy.deepcopy(locales)
    missing_by_locale = {code: set(english) - set(data) for code, data in locales.items()}

    if any(missing_by_locale.values()) and client is None:
        raise DeepLAPIError(f"Set {DEEPL_AUTH_KEY_ENV} before translating missing locale strings.")

    if client is not None:
        unknown = sorted(code for code, keys in missing_by_locale.items() if keys and code not in LOCALE_TARGETS)
        if unknown:
            raise LocaleSyncError(f"No DeepL target-language mapping exists for: {', '.join(unknown)}")

        required = sum(
            sum(len(value) for value in {english[key] for key in keys})
            for keys in missing_by_locale.values()
        )
        if required:
            client.ensure_quota(required)

        for code, missing_keys in missing_by_locale.items():
            if not missing_keys:
                continue
            texts = [english[key] for key in sorted(missing_keys)]
            translations = client.translate_many(LOCALE_TARGETS[code], texts)
            if set(translations) != set(texts):
                raise DeepLAPIError(f"DeepL returned incomplete translations for {code}.")
            candidates[code].update({key: translations[english[key]] for key in missing_keys})

    if prune:
        for code, data in candidates.items():
            candidates[code] = {key: data[key] for key in english if key in data}

    return candidates, missing_by_locale


def write_json_atomically(updates: dict[Path, dict[str, str]]) -> None:
    temporary_paths: dict[Path, Path] = {}
    try:
        for path, data in updates.items():
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                newline="\n",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                file.write(format_locale_json(data))
                file.flush()
                os.fsync(file.fileno())
                temporary_paths[path] = Path(file.name)
        for path, temporary_path in temporary_paths.items():
            os.replace(temporary_path, path)
    finally:
        for temporary_path in temporary_paths.values():
            temporary_path.unlink(missing_ok=True)


def print_warnings(report: dict[str, Any]) -> None:
    for code, keys in report["orphaned_by_locale"].items():
        if keys:
            print(f"Warning: {code}.json contains {len(keys)} orphaned key(s); use --prune to remove them.")
    for code, keys in report["empty_by_locale"].items():
        if keys:
            print(f"Warning: {code}.json contains {len(keys)} empty translation(s); existing values are preserved.")


def check_catalog(source_dir: Path, locales_dir: Path) -> int:
    paths = discover_locales(locales_dir)
    english = load_locale(paths.pop("en"))
    locales = {code: load_locale(path) for code, path in paths.items()}
    extracted = {canonical_entry(term)[0] for term in source_terms(source_dir)}
    report = validate_catalogs(extracted, english, locales)
    print_warnings(report)

    if report["missing_english"]:
        print(f"Error: en.json is missing {len(report['missing_english'])} extracted string(s).", file=sys.stderr)
    for code, keys in report["missing_by_locale"].items():
        if keys:
            print(f"Error: {code}.json is missing {len(keys)} English catalog key(s).", file=sys.stderr)
    if report["missing_english"] or any(report["missing_by_locale"].values()):
        return 1
    print("Locale catalogs are complete.")
    return 0


def translate_catalog(source_dir: Path, locales_dir: Path, prune: bool) -> int:
    paths = discover_locales(locales_dir)
    english_path = paths.pop("en")
    existing_english = load_locale(english_path)
    locales = {code: load_locale(path) for code, path in paths.items()}
    terms = source_terms(source_dir)
    extracted = {canonical_entry(term)[0] for term in terms}
    english, added = update_english_catalog(existing_english, terms)

    missing = {code: set(english) - set(data) for code, data in locales.items()}
    client = None
    if any(missing.values()):
        client = DeepLClient(os.getenv(DEEPL_AUTH_KEY_ENV, ""))

    candidates, missing = locale_candidates(english, locales, client, prune)
    updates: dict[Path, dict[str, str]] = {}
    if english != existing_english:
        updates[english_path] = english
    for code, data in candidates.items():
        if data != locales[code]:
            updates[paths[code]] = data

    report = validate_catalogs(extracted, english, candidates)
    print_warnings(report)
    if not updates:
        print("Locale catalogs are already synchronized; DeepL was not called.")
        return 0

    write_json_atomically(updates)
    translated_count = sum(len(keys) for keys in missing.values())
    print(f"Added {len(added)} English string(s) and translated {translated_count} missing locale value(s).")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronize auto-mcs locale catalogs.")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--translate", action="store_true", help="translate missing locale entries with DeepL")
    modes.add_argument("--check", action="store_true", help="validate catalogs without writing files or calling DeepL")
    parser.add_argument("--prune", action="store_true", help="remove locale keys no longer present in the English catalog (only with --translate)")
    args = parser.parse_args(argv)
    if args.prune and not args.translate:
        parser.error("--prune requires --translate")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_dir, locales_dir = project_paths()
    try:
        return translate_catalog(source_dir, locales_dir, args.prune) if args.translate else check_catalog(source_dir, locales_dir)
    except LocaleSyncError as error:
        print(f"Locale synchronization failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
