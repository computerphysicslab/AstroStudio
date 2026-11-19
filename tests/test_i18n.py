"""Translation dictionary tests."""

from astrostudio.core.i18n import Translator


def test_translation_falls_back_to_english():
    english = Translator("en")
    assert english.tr("File") == "File"
    assert Translator("es").tr("File") == "Archivo"
    assert Translator("de").tr("Open") == "Öffnen"
    assert Translator("ja").tr("Export / Save As") == "エクスポート／名前を付けて保存"
    assert Translator("ru").tr("File") == "Файл"
    assert Translator("zh").tr("File") == "文件"
    assert Translator("xx").tr("File") == "File"
