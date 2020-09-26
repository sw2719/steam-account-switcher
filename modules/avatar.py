import aiohttp
import json
import shutil
import os
import sys
import asyncio
from io import BytesIO

API_KEY = '88CA6F49C590BF8B498AF4FCFB9964F1'
PY_VERSION = float(f'{sys.version_info[0]}.{sys.version_info[1]}')

if PY_VERSION >= 3.8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

elif PY_VERSION <= 3.4:
    print('Not supported Python version. At least 3.5 is required.')
    sys.exit(0)


def download_avatar(steamid_list):
    '''Downloads avatar images through Steam API.
    param steamid_list: A list containing steamid64'''

    if not os.path.isdir('avatar'):
        os.mkdir('avatar')

    async def download_image(steamid64):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={API_KEY}&steamids={steamid64}', timeout=5) as r:
                    data = json.loads(await r.text())
                    image_url = data['response']['players'][0]['avatarmedium']
                    print(f'Found image URL for {steamid64}')

                async with session.get(image_url) as r:
                    print(f'Downloading {image_url} for {steamid64}...')

                    with open(f'avatar/{steamid64}.jpg', 'wb') as f:
                        shutil.copyfileobj(BytesIO(await r.read()), f)
        except (aiohttp.ClientError, OSError):
            print(f'Exception while downloading image for {steamid64}')

    if PY_VERSION >= 3.7:
        async def main():
            tasks = [asyncio.create_task(download_image(steamid)) for steamid in steamid_list]
            await asyncio.gather(*tasks)

        asyncio.run(main())
    else:
        async def main():
            futures = [asyncio.ensure_future(download_image(steamid)) for steamid in steamid_list]
            await asyncio.gather(*futures)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
