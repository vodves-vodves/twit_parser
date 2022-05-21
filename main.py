import re
import requests
import glob
import logging
import time
import sys

from pprint import pprint
from datetime import datetime
from logging import StreamHandler, Formatter

timetoday = datetime.today().strftime("%H:%M:%S")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(Formatter(fmt='[%(asctime)s]: %(message)s'))
logger.addHandler(handler)


def net_to_cookie(filename: str, service: str):
    cookies = {}
    try:
        with open(filename, 'r', encoding='utf-8') as fp:
            for line in fp:
                try:
                    if not re.match(r'^\#', line) and service in line:
                        lineFields = line.strip().split('\t')
                        cookies[lineFields[5]] = lineFields[6]
                except:
                    continue
    except UnicodeDecodeError:
        with open(filename, 'r') as fp:
            for line in fp:
                try:
                    if not re.match(r'^\#', line) and service in line:
                        lineFields = line.strip().split('\t')
                        cookies[lineFields[5]] = lineFields[6]
                except:
                    continue
    return cookies


def get_link(name):
    res = []
    logs = glob.glob('cookies//*')
    for log in logs:
        cookie = net_to_cookie(log, 'twitter')

        url_get_bear = 'https://abs.twimg.com/responsive-web/client-web/main.3805b556.js'
        try:
            r = requests.get(url_get_bear)
            auth = r.text.split('r="ACTION_FLUSH"')[-1].split(',s="')[1].split('"')[0]
        except:
            logger.error("Не удалось получить токен пользователя!")
        bearer_token = f'Bearer {auth}'

        csrf_token = cookie['ct0']

        headers_tw = {
            'accept': '*/*',
            'x-origin': 'https://twitter.com',
            'authorization': bearer_token,
            'x-csrf-token': csrf_token,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36'
        }

        def get_user_id():
            url_get_id = 'https://twitter.com/i/api/graphql/Bhlf1dYJ3bYCKmLfeEQ31A/UserByScreenName'
            variables = {
                'variables': {"screen_name": name, "withSafetyModeUserFields": True, "withSuperFollowsUserFields": True}
            }
            try:
                r = requests.get(url_get_id, headers=headers_tw, cookies=cookie, json=variables).json()
                return r['data']['user']['result']['rest_id']
            except:
                logger.error("Не удалось получить ID пользователя!")

        url_get_tweets = 'https://twitter.com/i/api/graphql/5NOBJXe6JipHc2MqvOAjxQ/UserTweets'

        data = {
            'variables': {"userId": get_user_id(), "count": 5, "includePromotedContent": False,
                          "withQuickPromoteEligibilityTweetFields": False, "withSuperFollowsUserFields": True,
                          "withDownvotePerspective": False, "withReactionsMetadata": False,
                          "withReactionsPerspective": False,
                          "withSuperFollowsTweetFields": False, "withVoice": False, "withV2Timeline": True},
            'features': {"dont_mention_me_view_api_enabled": True, "interactive_text_enabled": True,
                         "responsive_web_uc_gql_enabled": False, "responsive_web_edit_tweet_api_enabled": False}
        }
        try:
            r = requests.get(url_get_tweets, headers=headers_tw, cookies=cookie,
                             json=data).json()

            d = r['data']['user']['result']['timeline_v2']['timeline']['instructions']
            r = d[1]

            for i in r['entries']:
                try:
                    res.append(i['content']['itemContent']['tweet_results']['result']['legacy']['full_text'])
                except:
                    continue
        except KeyError:
            logger.error("Не удалось получить твиты")

    return res


def discord_enter(url):
    try:
        with open('tokens/tokens.txt', 'r', encoding='utf-8') as f:
            for token in f:
                try:
                    url_invite = f'https://discord.com/api/v9/invites/{url}'
                    headers_dis = {
                        'accept': '*/*',
                        'authorization': token,
                        'referer': 'https://discord.com/channels/@me',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36'
                    }
                    p = requests.post(url_invite, headers=headers_dis).json()
                    try:
                        name_channel = p['guild']['name']
                    except:
                        logger.error("Не удалось получить название канала")
                    return name_channel
                except:
                    logger.error("Ошибка при входе в дискорд канал")
    except EnvironmentError:
        logger.error("Файл с токенами дискорда не существует")
        # нужен выход


if __name__ == "__main__":
    twitter_name = input('Введите ник твиттера без собачки: (Пример: Стандартный никнейм - @nickname\n'
                         '                                           Требуемый для ввода никнейм - nickname\n')
    req_sec = input('Введите через какое количество секунд отправлять запросы: ')
    finding = True
    while finding:
        res = get_link(twitter_name)
        link = ''
        logger.debug('Поиск ссылок...')
        for i in res:
            try:
                i = i.split('https://t.co')[1].split(' ')[0]
                link = f'https://t.co{i}'
                try:
                    r = requests.get(link).text
                    link = r.split('meta property="og:url" content="https://discord.com/invite/')[1].split('" />')[0]
                    name_channel = discord_enter(link)
                    logger.debug(f'Вход успешно выполнен! Название канала: {name_channel}')
                    finding = False
                    break
                except:
                    logger.error('Получена не инвайт ссылка')
            except:
                continue
        time.sleep(int(req_sec))

# {"code": "smUXXnUj", "type": 0, "expires_at": "2022-05-26T02:30:14+00:00", "guild": {"id": "976673093336563723", "name": "\u0421\u0435\u0440\u0432\u0435\u0440 piplist", "splash": null, "banner": null, "description": null, "icon": null, "features": [], "verification_level": 0, "vanity_url_code": null, "premium_subscription_count": 0, "nsfw": false, "nsfw_level": 0}, "channel": {"id": "976673093336563726", "name": "general", "type": 0}, "inviter": {"id": "416578842941980684", "username": "piplist", "avatar": "50bf38d0a508a1e71e1d97a5baa45b4d", "avatar_decoration": null, "discriminator": "0668", "public_flags": 1048576}, "new_member": true}
