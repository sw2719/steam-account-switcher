import requests as req
import json
import shutil
import os
from io import BytesIO
from modules.account import loginusers

API_KEY = '88CA6F49C590BF8B498AF4FCFB9964F1'


def download_avatar(steamid_list=loginusers()[0]):
    '''Downloads avatar images through Steam API.
    param steamid_list: A list containing steamid64'''

    dl_list = []
    if not os.path.isdir('avatar'):
        os.mkdir('avatar')

    for steamid in steamid_list:
        try:
            with req.get(f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={API_KEY}&steamids={steamid}', timeout=5) as r:
                r.raise_for_status()
                data = json.loads(r.text)
                dl_list.append(data['response']['players'][0]['avatarmedium'])
                print(f'Found image URL for {steamid}')

        except req.RequestException:
            continue

    for index, url in enumerate(dl_list):
        try:
            with req.get(url, timeout=5) as r:
                r.raise_for_status()
                print(f'Downloading {url}...')
                with open(f'avatar/{steamid_list[index]}.jpg', 'wb') as f:
                    shutil.copyfileobj(BytesIO(r.content), f)

        except req.RequestException:
            continue
