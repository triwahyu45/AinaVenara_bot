from aina_companion.secrets import KeyringSecretStore, MemorySecretBackend


def test_secret_store_uses_backend_not_project_file():
    backend = MemorySecretBackend()
    store = KeyringSecretStore(backend)
    store.set("profile", "secret-value")
    assert store.get("profile") == "secret-value"
    store.delete("profile")
    assert store.get("profile") is None

