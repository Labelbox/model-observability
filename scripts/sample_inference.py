import time
import requests

images = [
    "https://www.allthingssupplychain.com/wp-content/uploads/2021/05/GettyImages-1266433901-1-1170x779.jpg",
    "https://media.wired.com/photos/5a035e6f06eea65aaa281ea2/master/w_2560%2Cc_limit/cargoship-TA.jpg",
    "https://wallpapercave.com/wp/wp2074610.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/60/USSRankin.jpg",
    "https://acadiamagic.com/1200w/sorrento-0722.jpg",
    "https://www.maritime-executive.com/media/images/article/Photos/Ports/New-York-New-Jersey-container-port-Port-Authority-of-NY-NJ.61d93c.jpg",
    "https://mklstatic01.azureedge.net/~/media/specialty/marine/tips-for-docking-boat.jpg",
    "https://moneyislandmarina.com/wp-content/uploads/2016/03/dry-docked-boats-at-Money-Island-Marina-768x510.jpg"
]

for idx, url in enumerate(images):
    print(f"Making request {idx}")
    r = requests.post("http://0.0.0.0:5100/predict",
                      files={'image': requests.get(url).content})
    time.sleep(3)
