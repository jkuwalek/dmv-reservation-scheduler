from dmvwatch.adapters.db.tables import Base


def test_every_expected_table_is_mapped() -> None:
    assert set(Base.metadata.tables) == {
        "watch",
        "watch_office_mute",
        "credential",
        "slot_observation",
        "notification",
    }


def test_observations_are_indexed_for_the_lookup_the_sweep_does() -> None:
    table = Base.metadata.tables["slot_observation"]
    indexed = {tuple(c.name for c in index.columns) for index in table.indexes}
    assert ("office_id", "transaction_type", "observed_at") in indexed


def test_a_credential_is_removed_with_its_watch() -> None:
    table = Base.metadata.tables["credential"]
    fk = next(iter(table.c.watch_id.foreign_keys))
    assert fk.ondelete == "CASCADE"
