from abc import ABC, abstractmethod


class TranslationProvider(ABC):
    @abstractmethod
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str: ...

    @abstractmethod
    async def health(self) -> dict: ...

    @abstractmethod
    def provider_name(self) -> str: ...
