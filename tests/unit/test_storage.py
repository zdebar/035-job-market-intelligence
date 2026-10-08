import hashlib
import json

from job_market_intelligence.ingestion.http_client import HttpResponse
from job_market_intelligence.ingestion.storage import save_raw_response


def test_save_raw_response_writes_metadata_without_changing_payload(tmp_path) -> None:
    payload = b'{"jobs":[]}'
    response = HttpResponse(
        status_code=200,
        headers={"content-type": "application/json"},
        content=payload,
    )

    response_path = save_raw_response(
        project_root=tmp_path,
        storage_directory="data/01_bronze/greenhouse",
        source_id="greenhouse",
        method="GET",
        endpoint="https://example.test/jobs",
        response=response,
        request={"content": "true"},
        record_count=0,
    )

    metadata = json.loads(response_path.with_name("metadata.json").read_text())

    assert response_path.read_bytes() == payload
    assert metadata["run_id"] == response_path.parent.name
    assert metadata["http_method"] == "GET"
    assert metadata["payload_sha256"] == hashlib.sha256(payload).hexdigest()
    assert metadata["payload_size_bytes"] == len(payload)
    assert metadata["record_count"] == 0
