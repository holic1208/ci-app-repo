import pytest
from moto import mock_aws
import boto3
import json
from random_rank import app, save_winner_to_s3

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@mock_aws
def test_homepage_loads(client):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="for-cicd-test-tournament-s3") # please edit this part

    response = client.get("/")
    assert response.status_code == 200
    assert "16강" in response.data.decode("utf-8")

    for _ in range(8):
        response = client.post("/choose", data={"choice": "https://example.com/link1"})
        assert response.status_code == 200

    assert "8강" in response.data.decode("utf-8")

    for _ in range(4):
        response = client.post("/choose", data={"choice": "https://example.com/link1"})
        assert response.status_code == 200

    assert "4강" in response.data.decode("utf-8")

    for _ in range(2):
        response = client.post("/choose", data={"choice": "https://example.com/link1"})
        assert response.status_code == 200

    assert "결승" in response.data.decode("utf-8")

    response = client.post("/choose", data={"choice": "https://example.com/link1"})
    save_winner_to_s3("https://example.com/link1", s3_client=s3)
    assert response.status_code == 200
    assert "당신의 선택은 이 곡입니다" in response.data.decode("utf-8")

    print(response.data.decode("utf-8"))

def test_invalid_route(client):
    response = client.get("/invalid_route")
    assert response.status_code == 404
    assert b"Not Found" in response.data
