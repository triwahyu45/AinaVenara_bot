import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from aina_companion.memory import LegacyDatabaseError, MemoryStore


def assert_uuid(value: str) -> None:
    assert str(uuid.UUID(value)) == value


def test_memory_context_keeps_recent_messages_and_enabled_facts(tmp_path):
    memory = MemoryStore(tmp_path / "memory.sqlite3")
    session = memory.create_session()
    fact = memory.add_fact("User suka kopi.")
    disabled_fact = memory.add_fact("Fakta sementara.")
    memory.update_fact(disabled_fact, "Fakta sementara.", enabled=False)
    for number in range(5):
        memory.add_message(session, "user", f"pesan {number}")
    memory.set_summary(session, "Ringkasan lama.")

    context = memory.context(session, 2)

    assert_uuid(session)
    assert_uuid(fact)
    assert context["summary"] == "Ringkasan lama."
    assert context["facts"] == ["User suka kopi."]
    assert [message["content"] for message in context["messages"]] == ["pesan 3", "pesan 4"]
    memory.close()


def test_schema_migration_is_versioned_and_idempotent(tmp_path):
    path = tmp_path / "memory.sqlite3"
    memory = MemoryStore(path)
    assert memory.schema_version() == 1
    memory.close()

    reopened = MemoryStore(path)
    assert reopened.schema_version() == 1
    assert reopened.db.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
    reopened.close()


def test_session_messages_persist_after_restart(tmp_path):
    path = tmp_path / "memory.sqlite3"
    memory = MemoryStore(path)
    session = memory.create_session("Sesi persist")
    message = memory.add_message(session, "user", "Halo Aina")
    assert_uuid(message)
    memory.close()

    reopened = MemoryStore(path)
    assert reopened.ensure_session(session) == session
    assert reopened.message_count(session) == 1
    assert reopened.recent_messages(session, 10)[0]["content"] == "Halo Aina"
    reopened.close()


def test_foreign_key_rejects_unknown_session_and_cascades_delete(tmp_path):
    memory = MemoryStore(tmp_path / "memory.sqlite3")
    session = memory.create_session()
    memory.add_message(session, "user", "hapus bersama sesi")

    with pytest.raises(sqlite3.IntegrityError):
        memory.add_message(str(uuid.uuid4()), "user", "sesi tidak ada")

    memory.delete_session(session)
    assert memory.message_count(session) == 0
    memory.close()


def test_invalid_message_role_is_rejected(tmp_path):
    memory = MemoryStore(tmp_path / "memory.sqlite3")
    session = memory.create_session()
    with pytest.raises(ValueError, match="Role pesan tidak valid"):
        memory.add_message(session, "assistant", "role lama tidak boleh lolos")
    memory.close()


def test_fact_crud_uses_uuid_text_ids(tmp_path):
    memory = MemoryStore(tmp_path / "memory.sqlite3")
    fact = memory.add_fact("User suka teh.")
    assert_uuid(fact)

    memory.update_fact(fact, "User suka kopi.")
    assert memory.facts()[0]["content"] == "User suka kopi."

    memory.delete_fact(fact)
    assert memory.facts() == []
    memory.close()


def test_clear_memory_keeps_schema_ready_for_new_session(tmp_path):
    memory = MemoryStore(tmp_path / "memory.sqlite3")
    session = memory.create_session()
    memory.add_message(session, "user", "hapus")
    memory.add_fact("hapus")

    memory.clear()

    assert memory.sessions() == []
    assert memory.facts() == []
    assert memory.schema_version() == 1
    assert_uuid(memory.ensure_session())
    memory.close()


def test_unversioned_legacy_database_is_not_reused(tmp_path):
    path = tmp_path / "memory.sqlite3"
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY)")
    db.commit()
    db.close()

    with pytest.raises(LegacyDatabaseError, match="Database legacy tanpa versi"):
        MemoryStore(path)


def test_memory_store_can_be_used_by_background_worker(tmp_path):
    memory = MemoryStore(tmp_path / "memory.sqlite3")
    session = memory.create_session()

    def worker():
        memory.add_message(session, "user", "Pesan dari worker")
        return memory.context(session, 5)

    with ThreadPoolExecutor(max_workers=1) as executor:
        context = executor.submit(worker).result()

    assert [message["content"] for message in context["messages"]] == ["Pesan dari worker"]
    memory.close()


def test_memory_store_serializes_parallel_writes(tmp_path):
    memory = MemoryStore(tmp_path / "memory.sqlite3")
    session = memory.create_session()

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(lambda index: memory.add_message(session, "user", f"pesan {index}"), range(20)))

    assert memory.message_count(session) == 20
    memory.close()
