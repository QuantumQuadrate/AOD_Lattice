import requests
import time

while True:
    start = time.time()
    resp = requests.get("http://10.0.0.17:5000/get_image")
    print(len(resp.content))
    print(time.time() - start)