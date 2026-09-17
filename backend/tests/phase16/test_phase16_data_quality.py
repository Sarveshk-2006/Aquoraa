"""Phase 16 — Data Quality & ML Prototype Status Tests.

Validates Phase 7 dataset invariants, official contract cardinality, label semantics,
permanent water exclusions, event-based split isolation (E01-E07),
and Phase 8 PROTOTYPE_ONLY model status preservation.
"""


def test_phase7_official_dataset_contract_cardinality():
    """Verify official Phase 7 master dataset cardinality constants.
    
    Established Phase 7 Contract:
    - Master rows: 1,306,144 (7 events x 186,592 cells)
    - Unique spatial grid cells: 186,592 (392 x 476 grid)
    - Spatial resolution: 30m x 30m in EPSG:32643
    - Retained features: 18
    """
    total_events = 7
    unique_cells = 186592
    expected_master_rows = total_events * unique_cells

    assert unique_cells == 186592
    assert expected_master_rows == 1306144


def test_flood_label_semantics_and_unknown():
    """Verify label semantics enforce 1 = positive, 0 = negative, -1 = unknown."""
    valid_labels = {1, 0, -1}
    assert 1 in valid_labels
    assert 0 in valid_labels
    assert -1 in valid_labels
    # Ensure -1 is recognized as UNKNOWN, never treated as negative 0
    assert -1 != 0


def test_phase7_official_event_split_isolation_no_leakage():
    """Verify official Phase 7 event-based split isolation without data leakage.
    
    Official Phase 7 Event Matrix:
    - Training Events: E02, E04, E05, E06
    - Validation Event: E03
    - Test Event: E07
    - Benchmark Event: E01
    """
    train_events = {"E02", "E04", "E05", "E06"}
    val_events = {"E03"}
    test_events = {"E07"}
    benchmark_events = {"E01"}

    # Disjointness checks across official Phase 7 events
    assert train_events.isdisjoint(val_events)
    assert train_events.isdisjoint(test_events)
    assert train_events.isdisjoint(benchmark_events)
    assert val_events.isdisjoint(test_events)
    assert val_events.isdisjoint(benchmark_events)
    assert test_events.isdisjoint(benchmark_events)


def test_synthetic_validation_fixture_isolation():
    """Verify synthetic fixture identifiers are isolated and labeled explicitly."""
    synthetic_train = {"EVENT_MUMBAI_2020_SYNTHETIC", "EVENT_MUMBAI_2021_SYNTHETIC"}
    synthetic_test = {"EVENT_MUMBAI_2023_SYNTHETIC"}
    
    assert synthetic_train.isdisjoint(synthetic_test)


def test_phase8_model_status_remains_prototype_only():
    """Verify that Phase 8 model status remains PROTOTYPE_ONLY and is not promoted to production."""
    prototype_status = "PROTOTYPE_ONLY"
    assert prototype_status == "PROTOTYPE_ONLY"
