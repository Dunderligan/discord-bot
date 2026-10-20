"""
Script that defines the standard network requests that the API will make,
currently keeps track of the API endpoint and key, which should be moved
if script will make requests to different APIs.
"""

import requests


class Network:
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.authorization = {"Authorization": f"Bearer {self.api_key}"}

    def get(self, endpoint: str, response_type):
        """Standard method for making a GET request to the API."""
        response = requests.get(
            url=f"{self.api_endpoint}/{endpoint}", headers=self.authorization
        )
        if response.status_code == 200:
            return response_type.from_json(response.json())
        response.raise_for_status()

    def post(self, endpoint: str, json: dict, response_type):
        """Standard method for making a POST request to the API."""
        response = requests.post(
            url=f"{self.api_endpoint}/{endpoint}", headers=self.authorization, json=json
        )
        if response.status_code == 200:
            return response_type.from_json(response.json())
        response.raise_for_status()
