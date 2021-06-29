import time
from datetime import datetime
from random import shuffle
import requests


images = [
    "https://www.allthingssupplychain.com/wp-content/uploads/2021/05/GettyImages-1266433901-1-1170x779.jpg",
    "https://media.wired.com/photos/5a035e6f06eea65aaa281ea2/master/w_2560%2Cc_limit/cargoship-TA.jpg"
]

for idx, url in enumerate(images):
    print(f"Making request {idx}")
    r = requests.post("http://0.0.0.0:5100/predict", files={'image': requests.get(url).content})
    time.sleep(3)
