import requests

dog_image = "https://notesfromadogwalker.files.wordpress.com/2013/06/birdie-fence.jpg"
files = {'image': requests.get(dog_image).content}

url = "http://0.0.0.0:5000/predict"
r = requests.post(url, files=files)
print(r.status_code)
print(r.json())
