"""Translation dictionary tests."""

from astrostudio.core.i18n import Translator


def test_all_languages_cover_menus_and_panels():
    from astrostudio.core.i18n import TRANSLATIONS
    from astrostudio.ui.main_window import MENU_LAYOUT

    labels = set()

    def walk(items):
        for item in items:
            if item[0] is None:
                continue
            labels.add(item[0])
            if len(item) == 3:
                walk(item[2])

    for _group, items in MENU_LAYOUT:
        walk(items)
    panels = {
        "Backends (startup discovery)",
        "Metadata (ExifTool, read-only)",
        "Histogram (CLI data, click handles to stretch)",
        "Terminal Drawer",
        "Open Recent",
        "No recent images",
    }
    for language in ("es", "de", "ja", "ru", "zh"):
        missing = [
            key for key in labels | panels
            if not key.endswith("%") and key not in TRANSLATIONS[language]
        ]
        assert not missing, (language, missing)


def test_translation_falls_back_to_english():
    english = Translator("en")
    assert english.tr("File") == "File"
    assert Translator("es").tr("File") == "Archivo"
    assert Translator("de").tr("Open") == "Öffnen"
    assert Translator("ja").tr("Export / Save As") == "エクスポート／名前を付けて保存"
    assert Translator("ru").tr("File") == "Файл"
    assert Translator("zh").tr("File") == "文件"
    assert Translator("xx").tr("File") == "File"


def test_draw_segment_hint_translated():
    assert Translator("es").tr("Draw a segment") == "Dibujar segmento"
    assert Translator("de").tr("Draw a segment") == "Segment ziehen"


def test_external_failure_messages_are_localised():
    keys = (
        "External backend failure",
        "Connector output (literal)",
        "HiPS survey service unavailable",
        "Star matching failed",
        "SkyStacker catalog environment missing",
        "Invalid CLI argument order",
        "External backend error",
    )
    for language in ("es", "de", "ja", "ru", "zh"):
        translator = Translator(language)
        for key in keys:
            translated = translator.tr(key)
            assert translated != key, (language, key)
            assert translated.strip()


def test_shadow_loupe_help_is_translated():
    from astrostudio.core.i18n import SHADOW_LOUPE_HELP

    assert Translator("en").tr(SHADOW_LOUPE_HELP) == SHADOW_LOUPE_HELP
    for language in ("es", "de", "ja", "ru", "zh"):
        translated = Translator(language).tr(SHADOW_LOUPE_HELP)
        assert translated != SHADOW_LOUPE_HELP, language
        assert "255" in translated, language


def test_rotating_by_hint_translated():
    assert Translator("es").tr("Rotating by") == "Rotando"
