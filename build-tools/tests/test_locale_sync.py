import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "locale_sync.py"
SPEC = importlib.util.spec_from_file_location("locale_sync", SCRIPT_PATH)
locale_sync = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(locale_sync)


class FakeDeepLClient:
    def __init__(self, translations, fail=False):
        self.translations = translations
        self.fail = fail
        self.calls = []
        self.required_characters = None

    def ensure_quota(self, required_characters):
        self.required_characters = required_characters
        if self.fail:
            raise locale_sync.DeepLAPIError("quota unavailable")

    def translate_many(self, target_language, texts):
        self.calls.append((target_language, texts))
        if self.fail:
            raise locale_sync.DeepLAPIError("translation unavailable")
        return {text: self.translations[text] for text in texts}


class FakeResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.data


class LocaleSyncTests(unittest.TestCase):
    def test_deepl_endpoint_is_inferred_from_key_type(self):
        self.assertEqual(locale_sync.deepl_endpoint("free-key:fx"), locale_sync.DEEPL_FREE_ENDPOINT)
        self.assertEqual(locale_sync.deepl_endpoint("pro-key"), locale_sync.DEEPL_PRO_ENDPOINT)

    def test_locale_target_mapping_covers_checked_in_locale_files(self):
        locale_directory = SCRIPT_PATH.parents[1] / "locales"
        expected = {path.stem for path in locale_directory.glob("*.json")} - {"en"}
        self.assertTrue(expected.issubset(locale_sync.LOCALE_TARGETS))
        self.assertEqual(locale_sync.LOCALE_TARGETS["pt"], "PT-PT")

    def test_placeholder_shielding_round_trips_and_rejects_missing_tokens(self):
        original = "Use $$ at {path}; press Ctrl+S and $server$."
        shielded, tokens = locale_sync.shield_placeholders(original)
        self.assertEqual(
            locale_sync.restore_placeholders(
                'Utilisez <x id="0"/> à <x id="1"/> ; appuyez sur <x id="2"/> et <x id="3"/>.',
                tokens,
            ),
            "Utilisez $$ à {path} ; appuyez sur Ctrl+S et $server$.",
        )
        with self.assertRaises(locale_sync.DeepLAPIError):
            locale_sync.restore_placeholders("Utilisez <x id=\"0\"/>.", tokens)
        self.assertIn('<x id="0"/>', shielded)

    def test_batching_respects_requested_size_limit_and_keeps_order(self):
        texts = ["one", "two", "three"]
        base_size = len(
            json.dumps(
                locale_sync.translation_payload(["one"], "DE"),
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        batches = locale_sync.batch_texts(texts, "DE", maximum_bytes=base_size + 8)
        self.assertEqual([text for batch in batches for text in batch], texts)
        for batch in batches:
            payload_size = len(
                json.dumps(
                    locale_sync.translation_payload(batch, "DE"),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            self.assertLessEqual(payload_size, base_size + 8)
        with self.assertRaises(locale_sync.DeepLAPIError):
            locale_sync.batch_texts(["small", "x" * 500], "DE", maximum_bytes=base_size + 8)

    def test_translation_response_requires_exact_response_order_and_count(self):
        response = {"translations": [{"text": "eins"}, {"text": "zwei"}]}
        self.assertEqual(locale_sync.translation_response(response, 2), ["eins", "zwei"])
        with self.assertRaises(locale_sync.DeepLAPIError):
            locale_sync.translation_response(response, 3)

    def test_deepl_client_sends_protected_batched_json(self):
        requests = []

        def opener(request, timeout):
            requests.append(request)
            return FakeResponse({"translations": [{"text": 'Hallo <x id="0"/>'}]})

        client = locale_sync.DeepLClient("pro-key", opener=opener, sleeper=lambda _: None)
        result = client.translate_many("DE", ["Hello $$"])

        self.assertEqual(result, {"Hello $$": "Hallo $$"})
        self.assertEqual(requests[0].full_url, f"{locale_sync.DEEPL_PRO_ENDPOINT}/v2/translate")
        self.assertEqual(requests[0].get_header("Authorization"), "DeepL-Auth-Key pro-key")
        payload = json.loads(requests[0].data)
        self.assertEqual(payload["target_lang"], "DE")
        self.assertEqual(payload["text"], ['Hello <x id="0"/>'])

    def test_deepl_client_retries_rate_limits_and_rejects_invalid_credentials(self):
        attempts = []
        waits = []

        def rate_limited_once(request, timeout):
            attempts.append(request)
            if len(attempts) == 1:
                error = HTTPError(request.full_url, 429, "rate limited", {}, io.BytesIO())
                error.close()
                raise error
            return FakeResponse({"character_count": 1, "character_limit": 100})

        client = locale_sync.DeepLClient("pro-key", opener=rate_limited_once, sleeper=waits.append)
        self.assertEqual(client.usage(), (1, 100))
        self.assertEqual(waits, [1])

        def forbidden(request, timeout):
            error = HTTPError(request.full_url, 403, "forbidden", {}, io.BytesIO())
            error.close()
            raise error

        with self.assertRaises(locale_sync.DeepLAPIError):
            locale_sync.DeepLClient("bad-key", opener=forbidden, sleeper=lambda _: None).usage()

    def test_missing_values_are_translated_without_replacing_existing_values(self):
        english = {"hello": "Hello", "welcome": "Welcome", "again": "Hello"}
        locales = {"de": {"hello": "Hallo"}}
        client = FakeDeepLClient({"Hello": "Hallo neu", "Welcome": "Willkommen"})

        candidates, missing = locale_sync.locale_candidates(english, locales, client, prune=False)

        self.assertEqual(locales["de"], {"hello": "Hallo"})
        self.assertEqual(candidates["de"]["hello"], "Hallo")
        self.assertEqual(candidates["de"]["welcome"], "Willkommen")
        self.assertEqual(candidates["de"]["again"], "Hallo neu")
        self.assertEqual(missing["de"], {"welcome", "again"})
        self.assertEqual(client.required_characters, len("Hello") + len("Welcome"))
        self.assertEqual(client.calls, [("DE", ["Hello", "Welcome"])])

    def test_translation_failure_leaves_original_catalogs_unchanged(self):
        english = {"hello": "Hello"}
        locales = {"de": {}}
        client = FakeDeepLClient({}, fail=True)

        with self.assertRaises(locale_sync.DeepLAPIError):
            locale_sync.locale_candidates(english, locales, client, prune=False)
        self.assertEqual(locales, {"de": {}})

    def test_prune_removes_only_target_locale_orphans(self):
        english = {"present": "Present", "legacy": "Legacy"}
        locales = {"de": {"present": "Vorhanden", "legacy": "Alt", "orphan": "Veraltet"}}

        candidates, _ = locale_sync.locale_candidates(english, locales, client=None, prune=True)

        self.assertEqual(candidates["de"], {"present": "Vorhanden", "legacy": "Alt"})
        self.assertIn("orphan", locales["de"])

    def test_check_reports_source_and_locale_coverage_gaps(self):
        report = locale_sync.validate_catalogs(
            {"present", "missing-in-english"},
            {"present": "Present", "missing-in-locale": "Missing"},
            {"de": {"present": "Vorhanden", "orphan": "Alt"}},
        )
        self.assertEqual(report["missing_english"], {"missing-in-english"})
        self.assertEqual(report["missing_by_locale"]["de"], {"missing-in-locale"})
        self.assertEqual(report["orphaned_by_locale"]["de"], {"orphan"})

    def test_atomic_writer_does_not_leave_temporary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "de.json"
            path.write_text('{"old": "Alt"}\n', encoding="utf-8")
            locale_sync.write_json_atomically({path: {"new": "Neu"}})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"new": "Neu"})
            self.assertFalse(list(Path(directory).glob("*.tmp")))

    def test_build_specs_keep_locales_in_packaged_binaries(self):
        root = SCRIPT_PATH.parents[1]
        for spec_name in ("auto-mcs.windows.spec", "auto-mcs.linux.spec", "auto-mcs.macos.spec"):
            self.assertIn("locales", (root / "build-tools" / spec_name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
