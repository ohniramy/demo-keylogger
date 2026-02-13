import requests
TOKEN = "8412508547:AAEJkzH1N3GJs1gcZIXgiSGrZdkNSvOqJME"
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
print(requests.get(url).json())