"""LLM duzenleme adiminin, konusmaci etiketlerini ham transkriptten farkli bir
konusmaciya kaydirip kaydirmadigini (yanlislikla) tespit eden dogrulama.

LLM, metni parcalara bolup ayri ayri duzenledigi icin bazen bir turun icerigini
yanlis konusmaciya atfedebiliyor (orn. bir konusmacinin cumlesi
digerine atfedilebilir). Bu modul, her duzenlenmis turu icerik benzerligiyle
en yakin ham tura eslestirip, o ham etiket icin "baskin" (en sik esleşen)
duzenlenmis etiketten sapan turleri uyari olarak dondurur. Model etiketleri
tutarli bir sekilde yeniden adlandirmissa (orn. KONUSMACI_00 -> "Konuk") bu
baskin-esleme yaklasimi sayesinde yanlis alarm vermez; sadece TUTARSIZ
(bazen bir isim, bazen baska bir isim/numara) atamalari yakalar.
"""

from __future__ import annotations

import difflib
import re
from collections import Counter

_TURN_PATTERN = re.compile(r"^([^:\n]{1,40}):\s*(.*)$", re.DOTALL)
_MIN_CONTENT_LENGTH = 20
_MIN_MATCH_RATIO = 0.5


def _parse_turns(text: str) -> list[tuple[str, str]]:
    """'ETIKET: metin' seklindeki bloklari (etiket, metin) ciftlerine ayirir."""
    turns: list[tuple[str, str]] = []
    for block in text.split("\n\n"):
        block = block.strip()
        match = _TURN_PATTERN.match(block)
        if match:
            turns.append((match.group(1).strip(), match.group(2).strip()))
    return turns


def find_speaker_consistency_warnings(raw_text: str, edited_text: str) -> list[str]:
    """Duzenlenmis metindeki turleri en cok benzeyen ham tura eslestirip,
    baskin eslemeden sapan (olasi yanlis konusmaciya atfedilmis) turler icin
    okunabilir uyari mesajlari dondurur. Sorun yoksa bos liste doner.
    """
    raw_turns = _parse_turns(raw_text)
    edited_turns = _parse_turns(edited_text)
    if not raw_turns or not edited_turns:
        return []

    matches: list[tuple[str, str, str]] = []
    for edited_label, edited_content in edited_turns:
        if len(edited_content) < _MIN_CONTENT_LENGTH:
            continue
        best_raw_label, best_ratio = None, 0.0
        for raw_label, raw_content in raw_turns:
            ratio = difflib.SequenceMatcher(None, edited_content[:200], raw_content[:200]).ratio()
            if ratio > best_ratio:
                best_ratio, best_raw_label = ratio, raw_label
        if best_raw_label is not None and best_ratio > _MIN_MATCH_RATIO:
            matches.append((best_raw_label, edited_label, edited_content[:70]))

    if not matches:
        return []

    votes_per_raw_label: dict[str, Counter] = {}
    for raw_label, edited_label, _ in matches:
        votes_per_raw_label.setdefault(raw_label, Counter())[edited_label] += 1
    dominant_edited_label = {
        raw_label: counter.most_common(1)[0][0] for raw_label, counter in votes_per_raw_label.items()
    }

    warnings: list[str] = []
    for raw_label, edited_label, snippet in matches:
        if edited_label != dominant_edited_label[raw_label]:
            warnings.append(
                f"Olasi konusmaci karismasi: \"{snippet}...\" ham transkriptte '{raw_label}' "
                f"iken duzenlenmiste '{edited_label}' olarak etiketlenmis "
                f"(bu konusma icin beklenen: '{dominant_edited_label[raw_label]}')."
            )
    return warnings
