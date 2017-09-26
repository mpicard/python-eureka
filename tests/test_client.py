from unittest import mock
from eureka_client import Client


class TestClient:

    def test_register(self, client):
        assert client.register()
