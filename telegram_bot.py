import requests
import urllib.parse

with open('token.txt') as fin:
    token = fin.read()

base_url = 'https://api.telegram.org/bot' + token 

def telegram_request(func):
    def decorator(*args, **kwargs):
        try:
            response = requests.post(**func(*args, **kwargs), timeout = 15)
        except Exception as e:
            print(str(e))
            return []
        data = response.json()
        if not data['ok']:
            raise Exception(data['description'])
        return data['result']
    return decorator

@telegram_request
def send_message(chat_id, text, **kwargs):
    data =  { 'chat_id'     : chat_id
            , 'text'        : text
            , 'parse_mode'  : 'Markdown'
            }
    data.update(**kwargs)
    return dict(url = base_url + '/sendMessage', json = data)

@telegram_request
def send_photo(chat_id, photo, **kwargs):
    data = {
        'chat_id'				: chat_id
    }
    data.update(**kwargs)
    files = {
        'photo'					: photo
    }
    return dict(url = base_url + '/sendPhoto', data = data, files = files)