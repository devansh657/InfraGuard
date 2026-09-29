from fastapi.testclient import TestClient

from backend.main import app


def _default_payload(client: TestClient) -> dict[str, object]:
    response = client.get("/model-info")
    assert response.status_code == 200
    return response.json()["feature_defaults"]


def test_health_endpoint_reports_system_state():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "InfraGuard AI"
    assert "ml_models_loaded" in payload
    assert "db_connected" in payload


def test_predict_rejects_get_with_clear_error():
    with TestClient(app) as client:
        response = client.get("/predict")

    assert response.status_code == 405
    assert response.json() == {"error": "Method not allowed. Use POST."}


def test_predict_rejects_invalid_payload():
    with TestClient(app) as client:
        response = client.post("/predict", json={"Packet_Size": "bad"})

    assert response.status_code == 422
    assert response.json() == {"error": "Invalid request payload"}


def test_predict_stores_history():
    with TestClient(app) as client:
        payload = _default_payload(client)
        prediction = client.post("/predict", json=payload)
        history = client.get("/history")

    assert prediction.status_code == 200
    assert "failure_probability" in prediction.json()
    assert "explanation" in prediction.json()
    assert history.status_code == 200
    assert len(history.json()["records"]) >= 1
    assert "features" in history.json()["records"][0]


def test_diagnose_returns_failure_and_anomaly_outputs():
    with TestClient(app) as client:
        payload = _default_payload(client)
        response = client.post("/diagnose", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "failure" in body
    assert "anomaly" in body
    assert "explanation" in body["failure"]


def test_ai_analyst_returns_root_cause_recommendations_and_drift():
    with TestClient(app) as client:
        payload = _default_payload(client)
        response = client.post("/ai/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["severity"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert 0 <= body["priority_score"] <= 100
    assert "incident_summary" in body
    assert isinstance(body["root_causes"], list)
    assert isinstance(body["recommendations"], list)
    assert "drift_score" in body["drift"]


def test_ai_what_if_compares_baseline_and_candidate():
    with TestClient(app) as client:
        baseline = _default_payload(client)
        candidate = dict(baseline)
        candidate["CPU_Usage"] = min(100, float(candidate["CPU_Usage"]) + 10)
        response = client.post(
            "/ai/what-if",
            json={"baseline": baseline, "candidate": candidate},
        )

    assert response.status_code == 200
    body = response.json()
    assert "baseline" in body
    assert "candidate" in body
    assert "risk_delta" in body
    assert "impact_summary" in body


def test_nova_briefing_returns_voice_ready_summary():
    with TestClient(app) as client:
        response = client.get("/ai/nova/briefing")

    assert response.status_code == 200
    body = response.json()
    assert body["assistant"] == "NOVA"
    assert "spoken_briefing" in body
    assert isinstance(body["system_panels"], list)
    assert isinstance(body["command_suggestions"], list)


def test_live_tick_replays_dataset_and_stores_prediction():
    with TestClient(app) as client:
        status = client.get("/live/status")
        tick = client.post("/live/tick")
        history = client.get("/history")

    assert status.status_code == 200
    assert status.json()["mode"] == "sequential_dataset_replay"
    assert tick.status_code == 200
    tick_body = tick.json()
    assert tick_body["source"] == "secured_telemetry_stream"
    assert "analysis" in tick_body
    assert "explanation" in tick_body
    assert history.status_code == 200
    assert any(row["id"] == tick_body["prediction_id"] for row in history.json()["records"])


def test_diagnose_rejects_values_outside_trained_dataset_range():
    with TestClient(app) as client:
        payload = _default_payload(client)
        payload["Packet_Size"] = 1
        response = client.post("/diagnose", json=payload)

    assert response.status_code == 400
    assert "outside trained dataset range" in response.json()["detail"]
    assert "Packet_Size" in response.json()["detail"]


def test_negative_dwt_feature_one_is_valid_when_inside_training_range():
    with TestClient(app) as client:
        payload = _default_payload(client)
        payload["DWT_Feature_1"] = -1.0
        response = client.post("/diagnose", json=payload)

    assert response.status_code == 200


def test_model_info_and_eda_endpoints_are_available():
    with TestClient(app) as client:
        model_info = client.get("/model-info")
        eda = client.get("/eda")
        benchmark = client.get("/benchmark-report")

    assert model_info.status_code == 200
    assert model_info.json()["target_column"] == "protected_risk_label"
    assert len(model_info.json()["base_feature_columns"]) == 21
    assert eda.status_code == 200
    assert eda.json()["available"] is True
    assert benchmark.status_code == 200
    assert benchmark.json()["available"] is True
    assert "model_results" in benchmark.json()["benchmark"]


def test_dev_cors_allows_localhost_and_loopback_frontend_origins():
    with TestClient(app) as client:
        localhost = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        loopback = client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert localhost.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert loopback.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
