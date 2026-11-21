"""Filename-derived plate-solving hints from a bundled offline catalog."""

import json
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

DEFAULT_CATALOG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "openngc_hints.json")

CATALOG_PATTERNS = (
    ("M", re.compile(r"\bM(?:essier)?\s*0*(\d{1,3})\b", re.IGNORECASE)),
    ("NGC", re.compile(r"\bNGC\s*0*(\d{1,5})\b", re.IGNORECASE)),
    ("IC", re.compile(r"\bIC\s*0*(\d{1,5})\b", re.IGNORECASE)),
    ("C", re.compile(r"\bC(?:aldwell)?\s*0*(\d{1,3})\b", re.IGNORECASE)),
)

GENERIC_NAME_WORDS = frozenset(
    (
        "nebula", "galaxy", "cluster", "open", "globular", "planetary",
        "reflection", "emission", "dark", "diffuse", "the", "and", "of",
    )
)


@dataclass(frozen=True)
class CatalogObject:
    ra: float
    dec: float
    ids: tuple
    names: tuple

    @property
    def label(self) -> str:
        return self.ids[0] if self.ids else (self.names[0] if self.names else "unknown")


@dataclass(frozen=True)
class Hint:
    obj: CatalogObject
    token: str
    source: str


_CATALOG_CACHE: Dict[str, List[CatalogObject]] = {}


def load_catalog(path: str = None) -> List[CatalogObject]:
    catalog_path = path or DEFAULT_CATALOG
    if catalog_path in _CATALOG_CACHE:
        return _CATALOG_CACHE[catalog_path]
    with open(catalog_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    objects = [
        CatalogObject(
            float(entry["ra"]),
            float(entry["dec"]),
            tuple(entry.get("ids", [])),
            tuple(entry.get("names", [])),
        )
        for entry in data.get("objects", [])
    ]
    _CATALOG_CACHE[catalog_path] = objects
    return objects


def extract_tokens(filename: str) -> Tuple[List[Tuple[str, str, str]], str]:
    base = os.path.basename(filename)
    tokens = []
    for prefix, pattern in CATALOG_PATTERNS:
        for match in pattern.finditer(base):
            tokens.append((prefix + str(int(match.group(1))), "catalog", match.group(0)))
    normalized = re.sub(r"[^a-z0-9]+", " ", base.lower()).strip()
    return tokens, normalized


def _distinctive_words(name: str) -> List[str]:
    return [
        word
        for word in re.findall(r"[a-z0-9]+", name.lower())
        if len(word) >= 4 and word not in GENERIC_NAME_WORDS
    ]


def _word_present(word: str, words: List[str]) -> bool:
    for candidate in words:
        if word == candidate:
            return True
        if (
            len(word) >= 6
            and abs(len(word) - len(candidate)) <= 1
            and SequenceMatcher(None, word, candidate).ratio() >= 0.86
        ):
            return True
    return False


def resolve_filename(filename: str, catalog: List[CatalogObject] = None) -> List[Hint]:
    objects = catalog if catalog is not None else load_catalog()
    tokens, normalized = extract_tokens(filename)
    hints: List[Hint] = []
    seen = set()
    for token, source, raw in tokens:
        compact = re.sub(r"\s+", "", token).lower()
        for obj in objects:
            ids = {re.sub(r"[^a-z0-9]", "", item.lower()) for item in obj.ids}
            if compact not in ids:
                continue
            key = (round(obj.ra, 4), round(obj.dec, 4))
            if key in seen:
                continue
            seen.add(key)
            hints.append(Hint(obj, raw, source))
    normalized_words = normalized.split()
    exact_names = []
    for obj in objects:
        for name in obj.names:
            if len(name) < 4:
                continue
            needle = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
            if needle and needle in normalized:
                exact_names.append((obj, name))
                break
    name_matches = exact_names
    if not name_matches and not tokens:
        name_matches = []
        for obj in objects:
            for name in obj.names:
                distinctive = _distinctive_words(name)
                if distinctive and all(
                    _word_present(word, normalized_words) for word in distinctive
                ):
                    name_matches.append((obj, name))
                    break
    for obj, name in name_matches:
        key = (round(obj.ra, 4), round(obj.dec, 4))
        if key in seen:
            continue
        seen.add(key)
        hints.append(Hint(obj, name, "name"))
    return hints


def unique_hint(filename: str, catalog: List[CatalogObject] = None) -> Optional[Hint]:
    hints = resolve_filename(filename, catalog)
    coordinates = {(round(item.obj.ra, 4), round(item.obj.dec, 4)) for item in hints}
    if len(coordinates) == 1:
        return hints[0]
    return None


def plate_center_argv(hint: Hint) -> List[str]:
    return ["--plate-center", "%.6f,%.6f" % (hint.obj.ra, hint.obj.dec)]
