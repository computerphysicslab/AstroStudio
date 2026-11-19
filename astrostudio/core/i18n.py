"""Minimal extensible translation dictionary for menus and common messages."""

TRANSLATIONS = {
    "en": {},
    "es": {
        "File": "Archivo",
        "Edit": "Editar",
        "Processing": "Procesado",
        "Astrometry": "Astrometría",
        "Arithmetic": "Aritmética",
        "Color": "Color",
        "Filter": "Filtro",
        "View": "Ver",
        "Options": "Opciones",
        "Help": "Ayuda",
        "Open": "Abrir",
        "Export / Save As": "Exportar / Guardar como",
        "Undo": "Deshacer",
        "Redo": "Rehacer",
        "Export": "Exportar",
        "Metadata": "Metadatos",
        "Stop job": "Detener proceso",
        "About": "Acerca de",
        "Astro Studio ready": "Astro Studio listo",
        "Preferences saved": "Preferencias guardadas",
        "Open an image first": "Abre primero una imagen",
    },
    "de": {
        "File": "Datei",
        "Edit": "Bearbeiten",
        "Processing": "Verarbeitung",
        "View": "Ansicht",
        "Options": "Optionen",
        "Help": "Hilfe",
        "Open": "Öffnen",
        "Export / Save As": "Exportieren / Speichern unter",
        "Undo": "Rückgängig",
        "Redo": "Wiederholen",
        "Metadata": "Metadaten",
        "About": "Über",
    },
}


class Translator:
    def __init__(self, language: str = "en") -> None:
        self.language = language if language in TRANSLATIONS else "en"

    def tr(self, text: str) -> str:
        return TRANSLATIONS.get(self.language, {}).get(text, text)
