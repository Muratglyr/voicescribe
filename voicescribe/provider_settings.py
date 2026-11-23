"""Dis servisler (OpenRouter, Hugging Face) icin ortam degiskenlerinden okunan ayarlar.

Bu modul disinda hicbir yerde API anahtari, model adi ya da servis URL'si
sabit (hardcoded) olarak yazilmaz; tum degerler .env dosyasi / ortam
degiskenleri araciligiyla disaridan saglanir.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OpenRouterSettings:
    """--duzenle adimi icin OpenRouter baglanti bilgileri."""

    api_key: str | None
    base_url: str | None
    model_name: str | None

    def is_complete(self) -> bool:
        """Duzenleme adimini calistirmak icin gereken tum degerler tanimli mi?"""
        return bool(self.api_key and self.base_url and self.model_name)

    @classmethod
    def from_env(cls) -> OpenRouterSettings:
        return cls(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url=os.environ.get("OPENROUTER_BASE_URL"),
            model_name=os.environ.get("OPENROUTER_MODEL"),
        )


@dataclass(frozen=True)
class DeepgramSettings:
    """--konusmaci-ayir adimi icin Deepgram baglanti bilgileri."""

    api_key: str | None
    model_name: str | None

    def is_complete(self) -> bool:
        """Konusmaci ayrimi adimini calistirmak icin gereken tum degerler tanimli mi?"""
        return bool(self.api_key and self.model_name)

    @classmethod
    def from_env(cls) -> DeepgramSettings:
        return cls(
            api_key=os.environ.get("DEEPGRAM_API_KEY"),
            model_name=os.environ.get("DEEPGRAM_MODEL"),
        )
