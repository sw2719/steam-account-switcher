STEAM64_IDENTIFIER = 76561197960265728


def steam64_to_3(steamid64):
    steamid3 = f'[U:1:{int(steamid64) - STEAM64_IDENTIFIER}]'
    return steamid3


def steam64_to_32(steamid64):
    steamid32 = f'{int(steamid64) - STEAM64_IDENTIFIER}'
    return steamid32


def steam64_to_2(steamid64):
    steamid_n = int(steamid64) - STEAM64_IDENTIFIER

    if steamid_n % 2 == 0:
        steamid_modulo = '0'
    else:
        steamid_modulo = '1'

    steamid2 = f'STEAM_0:{steamid_modulo}:{steamid_n // 2}'

    return steamid2
