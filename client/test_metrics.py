import requests

url = "http://0.0.0.0:5001/observe"

params = {'start_date': '25-03-2021', 'end_date': '31-03-2021'}
r = requests.get(url, params=params)
print(r.status_code)
print(r.json())
