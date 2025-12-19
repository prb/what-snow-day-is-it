import pytest
from src.data_client import NWCCDataClient

class TestNWCCDataClient:
    @pytest.fixture
    def client(self) -> NWCCDataClient:
        return NWCCDataClient()

    def test_fetch_station_data_success(self, client: NWCCDataClient, mocker):
        # Mock the requests.Session.get call
        mock_response = mocker.Mock()
        mock_response.json.return_value = [
            {
                "data": [
                    {
                        "values": [
                            {"date": "2024-11-01", "value": 1.0},
                            {"date": "2024-11-02", "value": 2.0},
                        ]
                    }
                ]
            }
        ]
        mock_response.raise_for_status.return_value = None
        mocker.patch.object(client.session, "get", return_value=mock_response)

        data = client.fetch_station_data("998:WA:SNTL", "WTEQ", "2024-11-01", "2024-11-02")
        
        assert len(data) == 2
        assert data[0]["date"] == "2024-11-01"
        assert data[0]["value"] == 1.0

    def test_fetch_station_data_empty(self, client: NWCCDataClient, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mocker.patch.object(client.session, "get", return_value=mock_response)

        assert client.fetch_station_data("998:WA:SNTL", "WTEQ", "2024-11-01", "2024-11-02") == []

    def test_fetch_station_data_error(self, client: NWCCDataClient, mocker):
        mock_response = mocker.Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mocker.patch.object(client.session, "get", return_value=mock_response)

        with pytest.raises(Exception, match="API Error"):
            client.fetch_station_data("998:WA:SNTL", "WTEQ", "2024-11-01", "2024-11-02")
