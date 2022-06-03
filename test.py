import requests
import urllib.parse

token = "5187998346:AAFPwXQsNR1EQi2e7osOswEsFHAjDxiTpMk"
chat_id = "907706827"

message = "Questa è una prova, non so perché cazzo non va niente"
requests.get(
    f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote(message)}&disable_notification=True"
)
