from job_market_intelligence import main


def test_package_exposes_main_entry_point() -> None:
    assert callable(main)
