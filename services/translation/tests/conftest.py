import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("TRANSLATION_PROVIDER", "opus-mt")

from app.main import app
from app.providers.m2m100_provider import M2M100Provider
from app.providers.opus_mt_provider import OpusMTProvider

_opus_mt_provider: OpusMTProvider | None = None
_m2m100_provider: M2M100Provider | None = None


def get_opus_mt_provider() -> OpusMTProvider:
    global _opus_mt_provider
    if _opus_mt_provider is None:
        settings_model_en_zh = os.environ.get("MODEL_EN_ZH", "Helsinki-NLP/opus-mt-en-zh")
        settings_model_zh_en = os.environ.get("MODEL_ZH_EN", "Helsinki-NLP/opus-mt-zh-en")
        _opus_mt_provider = OpusMTProvider(
            model_en_zh=settings_model_en_zh,
            model_zh_en=settings_model_zh_en,
        )
        _opus_mt_provider.load()
    return _opus_mt_provider


def get_m2m100_provider() -> M2M100Provider:
    global _m2m100_provider
    if _m2m100_provider is None:
        model_name = os.environ.get("M2M_MODEL", "facebook/m2m100_418M")
        _m2m100_provider = M2M100Provider(model_name=model_name)
        _m2m100_provider.load()
    return _m2m100_provider


@pytest.fixture(scope="session")
def opus_mt_provider() -> OpusMTProvider:
    return get_opus_mt_provider()


@pytest.fixture(scope="session")
def m2m100_provider() -> M2M100Provider:
    return get_m2m100_provider()


@pytest.fixture(scope="session")
def client(opus_mt_provider):
    import app.main as main_module
    main_module.provider = opus_mt_provider
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def m2m100_client(m2m100_provider):
    import app.main as main_module
    main_module.provider = m2m100_provider
    with TestClient(app) as c:
        yield c
