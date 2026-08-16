from types import SimpleNamespace

from aina_companion.audio import GoogleCloudSpeechListener, final_transcripts


def response(text, is_final=True):
    alternative = SimpleNamespace(transcript=text)
    result = SimpleNamespace(is_final=is_final, alternatives=[alternative])
    return SimpleNamespace(results=[result])


def test_final_transcripts_ignores_interim_and_blank_results():
    assert list(final_transcripts([response(" sementara ", False), response(" Halo "), response(" ")])) == [
        "Halo"
    ]


def test_cloud_listener_continuous_publishes_transcripts(monkeypatch):
    heard = []
    listener = GoogleCloudSpeechListener(heard.append, heard.append)
    monkeypatch.setattr(listener, "_stream", lambda *_args, **_kwargs: iter(["Halo Aina"]))

    listener.listen_continuous()
    listener._thread.join(timeout=1)

    assert heard == ["Halo Aina"]


def test_cloud_listener_mute_discards_transcript(monkeypatch):
    heard = []
    listener = GoogleCloudSpeechListener(heard.append, heard.append)
    listener.muted = True
    monkeypatch.setattr(listener, "_stream", lambda *_args, **_kwargs: iter(["Rahasia"]))

    listener.listen_continuous()
    listener._thread.join(timeout=1)

    assert heard == []


def test_cloud_listener_push_to_talk_returns_first_final_transcript(monkeypatch):
    listener = GoogleCloudSpeechListener(lambda _text: None, lambda _text: None)
    monkeypatch.setattr(listener, "_stream", lambda *_args, **_kwargs: iter(["Halo"]))
    assert listener.listen_once() == "Halo"
