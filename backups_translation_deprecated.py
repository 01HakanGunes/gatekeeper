# Dont read this file, it is just a backup

"""
Translation handler for Helsinki-NLP/opus-mt-tc-big-tr-en model.
Provides Turkish to English translation capabilities for the AI Agent system.
"""

from typing import Optional, Any
import logging
from transformers.pipelines import pipeline
import torch


class TranslationHandler:
    """
    Handler for the Helsinki-NLP/opus-mt-tc-big-tr-en translation model.
    Uses transformers pipeline for simplified usage.
    """

    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-tc-big-tr-en"):
        self.model_name = model_name
        self._pipeline: Optional[Any] = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._is_loaded = False

    @property
    def pipe(self) -> Any:
        """Lazy load translation pipeline."""
        if self._pipeline is None:
            logging.info(
                f"Loading translation pipeline for {self.model_name} on device: {self._device}"
            )
            self._pipeline = pipeline(
                "translation",
                model=self.model_name,
                device=0 if self._device == "cuda" else -1,
            )
            self._is_loaded = True
            logging.info("Translation pipeline loaded successfully")
        return self._pipeline

    def translate(self, text: str, max_length: int = 512) -> str:
        """
        Translate text from Turkish to English.

        Args:
            text (str): Turkish text to translate
            max_length (int): Maximum length of generated translation

        Returns:
            str: English translation

        Raises:
            ValueError: If input text is empty
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        try:
            # Use pipeline for translation
            result = self.pipe(
                text, max_length=max_length, num_beams=4, early_stopping=True
            )

            # Extract translation text from result
            if isinstance(result, list) and len(result) > 0:
                translation = result[0].get("translation_text", "")
            else:
                translation = str(result)

            return translation.strip()

        except Exception as e:
            logging.error(f"Translation failed: {str(e)}")
            raise RuntimeError(f"Translation failed: {str(e)}")

    def __call__(self, text: str, max_length: int = 512) -> str:
        """
        Allow using the instance directly as a callable function.

        Args:
            text (str): Turkish text to translate
            max_length (int): Maximum length of generated translation

        Returns:
            str: English translation
        """
        return self.translate(text, max_length)

    def is_available(self) -> bool:
        """Check if translation functionality is available."""
        return True

    def unload_model(self) -> None:
        """Unload pipeline from memory to free resources."""
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logging.info("Translation pipeline unloaded from memory")


# Create a singleton instance for reuse across the application
translator = TranslationHandler()
