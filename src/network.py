import requests

class Network:
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key


    def request(self, endpoint: str, method: str, json: dict, response_type):
        """
            Standard method for making network request that pass json data, and return
            a response object with a defined from_json function.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.api_endpoint}/{endpoint}"
        print(f"Sending request to {url}")

        response: requests.Response

        if method == "POST":
            response = requests.post(url=url, json=json, headers=headers)
        elif method == "GET":
            response = requests.get(url=url, headers=headers)
        else:
            print(f"ERROR: Missing support for method: {method}")

        if response.status_code == 200:
            return response_type.from_json(response.json())
        response.raise_for_status()
