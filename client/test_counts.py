import requests

images = [
    "https://hgtvhome.sndimg.com/content/dam/images/hgtv/fullset/2012/5/25/1/RWAP_pet-friendly-room-dog-window_s3x4.jpg.rend.hgtvcom.616.822.suffix/1400972675264.jpeg",
    "https://notesfromadogwalker.files.wordpress.com/2013/06/birdie-fence.jpg",
    "https://st.hzcdn.com/fimgs/b432b5db0a63935c_5230-w500-h375-b0-p0--.jpg",
    "https://blog.healthypawspetinsurance.com/wp-content/uploads/Labrador_dog_pool_pond_backyard-compressor-e1492038155282.jpg",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRpJqBcpvHQ5fm23kxNTY0Mj6DcyllTLcvpioKsE5AcHNx3Io5HfCUtcirBtWc3epHlMqs&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_wMeyjHQEZBh6bCUpJgEtG5EhxX1TtRwyCA&usqp=CAU",
    "https://static.thebark.com/sites/default/files/content/article/full/dog_backyard_1.jpg",
    "https://www.dogingtonpost.com/wp-content/uploads/2018/09/8_playground-min.jpg",
    "https://i.pinimg.com/originals/f8/fa/cd/f8facdfc46dee7f72120c84ed4ea44ec.jpg",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQfQvF5zqpVW2OdKwLpP7SDK_0uxMEmbM_blg&usqp=CAU",
    "https://st.hzcdn.com/simgs/5ec10a55059469d5_8-9793/traditional-landscape.jpg",
    "https://www.hellomagazine.com/imagenes/homes/2020050689404/call-the-midwife-helen-george-chic-garden/0-428-484/helen-george-jack-ashton-dog-garden-z.jpg?ezimgfmt=rs:363x445/rscb5/ng:webp/ngcb5",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrvT-msveQuBjc-ByifBvR54UGi3s1kg0nSw&usqp=CAU",
    "https://hgtvhome.sndimg.com/content/dam/images/grdn/fullset/2014/11/2/0/CI_ci-xgrass-dog-runs-3.jpg.rend.hgtvcom.406.305.suffix/1452846042105.jpeg",
    "https://www.bunnings.co.nz/-/media/articles/outdoor/pets%20and%20wildlife/how%20to%20go%20pet%20friendly/header.jpg",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQVUgGcotAtf2A_CW8hDmu5PEqOxQLdUzG1TQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ7dbu6rpb52F5To5sNGRPCcSQOo57JAdd1YA&usqp=CAU",
    "https://nextluxury.com/wp-content/uploads/rustic-salvaged-wood-pallet-dog-fence-ideas.jpg",
    "https://i.ytimg.com/vi/J_WyWwRYAQ4/maxresdefault.jpg"
]

images_hard = [
    "https://iheartdogs.com/wp-content/uploads/2018/06/backyard-dangers-for-dogs.png",
    "https://cdn.shopify.com/s/files/1/0014/5060/6701/files/news_dog_run_ideas_cobblestone_accented_pet_run.jpg?1728432",
    "https://i.pinimg.com/originals/fa/8d/3b/fa8d3be0c3c13701c24dc0fe2f40c615.jpg",
    "https://m.media-amazon.com/images/S/aplus-media/sc/fe06c24a-b9a6-4ec2-b861-58ddb041ee2c.__CR0,0,970,600_PT0_SX970_V1___.jpg",
    "https://i.pinimg.com/originals/01/66/ca/0166cae6709a04076e8c05aabfe5be2a.jpg",
    "https://m.media-amazon.com/images/I/8194kJU+7DL._AC_UL320_.jpg",
    "https://barkandgoldphotography.com/wp-content/uploads/2018/08/family-mixed-dogs-backyard-session-pittsburgh-dog-photography.jpg",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8GUtmHFrsdRd2NtSM1WJ1PSTUcGB9Bm4jFg&usqp=CAU",
    "https://www.betterthanrealgrass.com/wp-content/uploads/2015/12/artificial-turf-dog-run-area-kidney-shape.jpg",
    "https://www.sunset.com/wp-content/uploads/2466fad8e0df559e749d9e0726667e7e-694x463-c-default.jpg",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQIXTRNIH75wvSYyPWk9-uTsVxEIe8IDygdOw&usqp=CAU",
]


def chunkIt(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0
    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg
    return out


import datetime
import time
import random


def run():
    today = datetime.datetime.now()
    easy_dates = [today - datetime.timedelta(days=i) for i in range(2, 6, 1)
                 ][::-1]
    easy_chunks = chunkIt(images, len(easy_dates))
    hard_dates = [today - datetime.timedelta(days=1), today]
    hard_chunks = chunkIt(images_hard, len(hard_dates))

    for url_chunks, dates, in [(easy_chunks, easy_dates),
                               (hard_chunks, hard_dates)]:
        for idx, urls in enumerate(url_chunks):
            date = dates[idx].strftime('%d-%m-%Y')
            for url in urls:
                files = {'image': requests.get(url).content}
                params = {'date': date}
                endpoint = "http://0.0.0.0:5000/predict"
                r = requests.post(endpoint, files=files, params=params)
                print(r.status_code)
                print(r.json())
                time.sleep(random.random() * 10)


while 1:
    try:
        run()
    except Exception as e:
        print("failed", e)