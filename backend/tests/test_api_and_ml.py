import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.trainers import TrainConfig, train_word_lid


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["paid_services"] is False


def test_analyze_endpoint(client):
    res = client.post("/api/analyze", json={"text": "Main university mein admission apply kar raha hoon.", "model_override": "dictionary"})
    assert res.status_code == 200
    body = res.json()
    assert body["code_switching"]["status"] == "YES"
    assert body["summary"]["total_words"] > 0


def test_dataset_seeded(client):
    res = client.get("/api/datasets")
    assert res.status_code == 200
    names = [d["name"] for d in res.json()["datasets"]]
    assert "sample_code_switching" in names


def test_preprocess_endpoint(client):
    res = client.post("/api/preprocess", json={"text": "Achha hai", "roman_urdu_normalize": True})
    assert res.status_code == 200
    assert "with_preprocessing" in res.json()


def test_research_notes(client):
    create = client.post(
        "/api/research/notes",
        json={"title": "Test note", "category": "Evaluation", "content": "Pipeline smoke test"},
    )
    assert create.status_code == 200
    note_id = create.json()["id"]
    listed = client.get("/api/research/notes")
    assert any(n["id"] == note_id for n in listed.json()["notes"])
    deleted = client.delete(f"/api/research/notes/{note_id}")
    assert deleted.status_code == 200


def test_train_persist_reload(tmp_path):
    X = ["main", "hai", "kar", "university", "admission", "apply", "report", "please", "to", "xyzabc"]
    y = [
        "URDU_ROMAN",
        "URDU_ROMAN",
        "URDU_ROMAN",
        "ENGLISH",
        "ENGLISH",
        "ENGLISH",
        "ENGLISH",
        "ENGLISH",
        "AMBIGUOUS",
        "UNKNOWN",
    ]
    # Expand tiny set
    X = X * 3
    y = y * 3
    result = train_word_lid(
        X[:20],
        y[:20],
        X[20:25],
        y[20:25],
        X[25:],
        y[25:],
        TrainConfig(model_type="logreg", random_seed=0, max_features=5000),
        artifact_dir=tmp_path,
    )
    assert "artifact_path" in result
    import joblib

    bundle = joblib.load(result["artifact_path"])
    pred1 = bundle["pipeline"].predict(["university"])[0]
    bundle2 = joblib.load(result["artifact_path"])
    pred2 = bundle2["pipeline"].predict(["university"])[0]
    assert pred1 == pred2


def test_report_export(client):
    res = client.post("/api/research/reports", json={"report_type": "complete", "format": "markdown"})
    assert res.status_code == 200
    assert "markdown" in res.json()["paths"]
