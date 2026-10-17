import pytest


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": None},
        {"text": 4},
        {"text": []},
        {"text": ""},
        {"text": " \t\n"},
        {"text": "x" * 5001},
        {"text": "hello", "extra": True},
    ],
)
def test_invalid_input(client, payload):
    assert client.post("/predict", json=payload).status_code == 422


@pytest.mark.parametrize(
    "text",
    ["a", "x" * 5000, "  hello world  ", "🙂" * 5000],
    ids=["minimum", "maximum-ascii", "trimmed", "maximum-unicode"],
)
def test_valid_length_boundaries(client, text):
    assert client.post("/predict", json={"text": text}).status_code == 200


def test_malformed_json(client):
    assert (
        client.post(
            "/predict", content='{"text":', headers={"Content-Type": "application/json"}
        ).status_code
        == 422
    )
