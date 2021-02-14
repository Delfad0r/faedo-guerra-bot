import itertools
import json
import requests
import urllib.parse

with open('token.txt') as fin:
    token = fin.read().strip()

base_url = 'https://api.telegram.org/bot' + token 

def telegram_request(func):
    def decorated(*args, **kwargs):
        while True:
            try:
                response = requests.post(**func(*args, **kwargs), timeout = 15)
            except Exception as e:
                print('Error: \'%s\' - Retrying' % str(e))
                continue
            data = response.json()
            if not data['ok']:
                print('Error: \'%s\' - Retrying' % data['description'])
                continue
            return data['result']
    return decorated

@telegram_request
def send_message(chat_id, text, **kwargs):
    data =  {
          'chat_id'             : chat_id
        , 'text'                : text
        , 'parse_mode'          : 'Markdown'
    }
    data.update(**kwargs)
    return dict(url = base_url + '/sendMessage', json = data)

@telegram_request
def send_photo(chat_id, photo, **kwargs):
    data = {
        'chat_id'               : chat_id
    }
    data.update(**kwargs)
    files = {
        'photo'	                : photo
    }
    return dict(url = base_url + '/sendPhoto', data = data, files = files)

@telegram_request
def send_document(chat_id, document, **kwargs):
    data = {
        'chat_id'               : chat_id
    }
    data.update(**kwargs)
    files = {
        'document'              : document
    }
    return dict(url = base_url + '/sendDocument', data = data, files = files)

@telegram_request
def send_photo_group(chat_id, media, **kwargs):
    data = {
        'chat_id'               : chat_id,
        'media'                 : json.dumps([{'type' : 'photo', 'media' : 'attach://%d' % i} for i in range(len(media))])
    }
    files = {str(i) : m for i, m in zip(itertools.count(), media)}
    return dict(url = base_url + '/sendMediaGroup', data = data, files = files)

@telegram_request
def set_chat_description(chat_id, description, **kwargs):
    data = {
          'chat_id'             : chat_id
        , 'description'         : description
    }
    data.update(**kwargs)
    return dict(url = base_url + '/setChatDescription', json = data)
