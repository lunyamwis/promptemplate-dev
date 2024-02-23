import requests

class APIScrapper:
    def __init__(self, url,headers) -> None:
        self.url = url
        self.headers = headers

    def scrap_users(self):
        resp = requests.get(self.url,headers=self.headers)
        return resp.json()