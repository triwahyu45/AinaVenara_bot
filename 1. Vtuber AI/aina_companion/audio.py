from __future__ import annotations

import audioop
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Any, Callable, Iterable


def save_pcm_wav(path: Path, pcm: bytes, rate: int = 24000) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(pcm)


def pcm_rms_levels(pcm: bytes, sample_rate: int = 24000, frame_ms: int = 50) -> list[float]:
    frame_bytes = max(2, int(sample_rate * frame_ms / 1000) * 2)
    levels = []
    for offset in range(0, len(pcm), frame_bytes):
        frame = pcm[offset : offset + frame_bytes]
        if frame:
            levels.append(min(1.0, audioop.rms(frame, 2) / 12000.0))
    return levels


class AudioPlayer:
    def __init__(self):
        import pygame

        pygame.mixer.init()
        self.pygame = pygame

    def play_pcm(self, pcm: bytes, on_level: Callable[[float], None] | None = None) -> float:
        temp = Path(tempfile.gettempdir()) / "aina_tts.wav"
        save_pcm_wav(temp, pcm)
        sound = self.pygame.mixer.Sound(str(temp))
        sound.play()
        if on_level:
            levels = pcm_rms_levels(pcm)

            def publish_levels():
                for level in levels:
                    on_level(level)
                    time.sleep(0.05)
                on_level(0.0)

            threading.Thread(target=publish_levels, daemon=True).start()
        return sound.get_length()


def final_transcripts(responses: Iterable[Any]) -> Iterable[str]:
    for response in responses:
        for result in response.results:
            if not result.is_final or not result.alternatives:
                continue
            transcript = result.alternatives[0].transcript.strip()
            if transcript:
                yield transcript


class GoogleCloudSpeechListener:
    """Google Cloud STT streaming microphone adapter."""

    def __init__(
        self,
        on_text: Callable[[str], None],
        on_error: Callable[[str], None],
        credentials_path: str = "",
    ):
        self.on_text = on_text
        self.on_error = on_error
        self.credentials_path = credentials_path
        self.muted = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _speech_client(self):
        from google.cloud import speech

        if self.credentials_path:
            return speech.SpeechClient.from_service_account_file(self.credentials_path)
        return speech.SpeechClient()

    def _requests(self, stream, speech):
        while not self._stop.is_set():
            data = stream.read(1600, exception_on_overflow=False)
            if data:
                yield speech.StreamingRecognizeRequest(audio_content=data)

    def _stream(self, language: str, device_index: int | None, single_utterance: bool = False):
        import pyaudio
        from google.cloud import speech

        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1600,
            input_device_index=device_index,
        )
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language,
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=False,
            single_utterance=single_utterance,
        )
        try:
            responses = self._speech_client().streaming_recognize(
                config=streaming_config,
                requests=self._requests(stream, speech),
            )
            yield from final_transcripts(responses)
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    def listen_continuous(self, language: str = "id-ID", device_index: int | None = None) -> None:
        self.stop()
        self._stop.clear()

        def worker():
            try:
                for transcript in self._stream(language, device_index):
                    if not self.muted:
                        self.on_text(transcript)
            except Exception as error:
                if not self._stop.is_set():
                    self.on_error(f"Google Cloud STT: {error}")

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def listen_once(self, language: str = "id-ID", device_index: int | None = None) -> str:
        self.stop()
        self._stop.clear()
        try:
            return next(iter(self._stream(language, device_index, single_utterance=True)))
        except StopIteration as error:
            raise RuntimeError("Google Cloud STT tidak menangkap ucapan.") from error
        finally:
            self._stop.set()

    def stop(self) -> None:
        self._stop.set()


SpeechListener = GoogleCloudSpeechListener
