import requests

url = "http://127.0.0.1:8000/phase1/brightness"
files = {'image': open('test.jpg', 'rb')}
data = {'brightness': 1.2, 'contrast': 1.1}  # Change dict for different features

response = requests.post(url, files=files, data=data)
if response.status_code == 200:
    with open("result.jpg", "wb") as f:
        f.write(response.content)
    print("API test image saved as result.jpg")
else:
    print("Error:", response.text)
