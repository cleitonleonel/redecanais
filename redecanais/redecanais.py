# -*- coding: utf-8 -*-
#
import re
import sys
import time
import shutil
import webbrowser
import http.server
import socketserver
import threading
import requests
from os import environ
from pychromecast import discovery, get_chromecasts
from redecanais.settings import URL_SERVER
from sys import platform as _sys_platform
from redecanais.player import html_player
from bs4 import BeautifulSoup

BASE_URL = URL_SERVER


def _get_platform():
    if 'ANDROID_ARGUMENT' in environ:
        return 'android'
    elif environ.get('KIVY_BUILD', '') == 'ios':
        return 'ios'
    elif _sys_platform in ('win32', 'cygwin'):
        return 'win'
    elif _sys_platform == 'darwin':
        return 'macosx'
    elif _sys_platform.startswith('linux'):
        return 'linux'
    elif _sys_platform.startswith('freebsd'):
        return 'linux'
    return 'unknown'


platform = _get_platform()
print(f'Sistema Operacional {platform} suportado!!!')


class ProxyRequests:
    def __init__(self):
        self.sockets = []
        self.acquire_sockets()
        self.proxies = self.mount_proxies()

    def acquire_sockets(self):
        response = requests.get('https://api.proxyscrape.com/?request=displayproxies&proxytype=http&timeout=7000&country=BR&anonymity=elite&ssl=yes').text
        self.sockets = response.split('\n')

    def mount_proxies(self):
        current_socket = self.sockets.pop(0)
        proxies = {
            'http': self.sockets,
        }
        return proxies


class SimpleServerHttp:
    handler = http.server.SimpleHTTPRequestHandler

    def __init__(self):
        print('initializing...')
        self.server = socketserver.TCPServer(("0.0.0.0", 9090), self.handler)
        print("Serving at port", 9090)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True

    def start(self):
        self.server_thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


class Browser(object):

    def __init__(self):
        self.request = None
        self.response = None
        self.proxies = None
        self.referer = None
        self.session = requests.Session()

    def headers(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
        }
        return headers

    def verify_proxy(self, url, proxies, data):
        with self.session as s:
            payload = data
            self.response = s.post(url=url, data=payload, proxies=proxies)
            if self.response.status_code == 200:
                print(proxies)
                self.proxies = proxies
                return True

    def set_proxies(self, **kwargs):
        if kwargs:
            self.proxies = kwargs
            return self.proxies
        else:
            self.proxies = ProxyRequests().proxies

    def send_request(self, method, url, **kwargs):
        if self.proxies:
            if type(self.proxies['http']) == list:
                for proxy in self.proxies['http']:
                    proxies = {
                        'http': 'http://' + proxy.replace('\r', ''),
                    }
                    result = self.verify_proxy(url, proxies, data=kwargs)
                    if result:
                        break

        response = self.session.request(method, url, proxies=self.proxies, **kwargs)
        if response.status_code == 200:
            self.referer = url
            return response.text

        return None


class ChannelsNetwork(Browser):

    def __init__(self, debug=False):
        self.debug = debug
        self.is_tv = False
        self.devices = []
        self.chromecasts = None
        self.browser = None
        self.url_server = None
        self.headers = self.headers()
        super().__init__()

    def search(self, parameter=None, description=True):
        self.url_server = URL_SERVER
        if type(parameter) is list:
            film_name = ' '.join(parameter).capitalize()
        elif parameter != '' and type(parameter) is str:
            film_name = parameter.capitalize()
        else:
            film_name = input('Digite o nome do filme que deseja assistir: ')
        data = {"queryString": film_name}
        url_search = f'{BASE_URL}/ajax_search.php'

        if self.debug:
            print('Search: ', url_search)
        return self.search_filmes(url_search, data, description=description)

    def get_links_categories(self, url, category):
        info_category = self.categories(url, category['category'].capitalize() + ' ')[0]
        html = self.send_request('GET', BASE_URL + info_category['url'])
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup.find('div', {'class': 'row pm-category-header-subcats'})
        films = tags.find_all('li')
        categories_list = []
        for info in films:
            result = info.a['href']
            categories_list.append(result)
        return categories_list

    def films(self, url, category, page=None):
        if type(category) is dict:
            categories_list = self.get_links_categories(url, category)
            for item in categories_list:
                if category['genre'] in item.lower():
                    pages = re.compile(r'videos-(.*?)-date').findall(item)[0]
                    url_category_films = BASE_URL + item.replace(pages, str(category['page']))
                    return self.films_per_category(url_category_films)
        else:
            info_category = self.categories(url, category.capitalize() + ' ')[0]
            pages = re.compile(r'videos(.*?)date').findall(info_category['url'])[0]
            if page is not None:
                url_category_films = BASE_URL + info_category['url'].replace(pages, '-' + str(page) + '-')
            else:
                url_category_films = BASE_URL + info_category['url'].replace(pages, str(category['page']))
            return self.films_per_category(url_category_films)

    def films_per_category(self, url):
        html = self.send_request('GET', url)
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup.find('ul', {'class': 'row pm-ul-browse-videos list-unstyled'})
        try:
            films = tags.find_all('div', {'class': 'pm-video-thumb'})
            films_list = []
            for info in films:
                result = info.find_all('a')[1]
                if 'https' not in result.img['data-echo']:
                    img = BASE_URL + result.img['data-echo']
                else:
                    img = result.img['data-echo']
                description = self.get_description(BASE_URL + result['href'])
                dict_films = {'title': result.img['alt'], 'url': BASE_URL + result['href'], 'img': img, 'description': description}
                films_list.append(dict_films)
            return films_list
        except ValueError:
            info_warning = soup.find('div', {'class': 'col-md-12 text-center'}).text
            print(info_warning)
            sys.exit()

    def search_filmes(self, url, data, description=None):
        url_genre = url
        html = self.send_request('POST', url_genre, data=data)
        if self.debug:
            print('Search Films: ', html)
        soup = BeautifulSoup(html, 'html.parser')
        films = soup.find_all('li')
        films_list = []

        if len(films) == 0:
            url = self.url_server + '/search.php?keywords=' + data['queryString'] + '&video-id='
            return self.films_per_genre(url)

        for info in films:
            if self.debug:
                print('Search Films: ', films)
            if ' - Episódio' not in info.a.text:
                result = info.a
                if description:
                    description = self.get_description(BASE_URL + result['href'])
                else:
                    description = None
                dict_films = {'title': result.text, 'url': BASE_URL + result['href'], 'img': '', 'description': description}
                films_list.append(dict_films)
            else:
                result = info.a
                dict_films = {'title': result.text, 'url': BASE_URL + result['href'], 'img': '', 'description': ''}
                films_list.append(dict_films)

        if self.debug:
            print('Search Films: ', films_list)
        return films_list

    def films_per_genre(self, url, category=None, genre=None):
        url_genre = url
        html = self.send_request('GET', url_genre)
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup.find('ul', {'class': 'row pm-ul-browse-videos list-unstyled'})
        films = tags.find_all('div', {'class': 'pm-video-thumb'})
        films_list = []
        for info in films:
            result = info.find_all('a')[1]
            if 'https' not in result.img['data-echo']:
                img = BASE_URL + result.img['data-echo']
            else:
                img = result.img['data-echo']
            description = self.get_description(BASE_URL + result['href'])
            dict_films = {'title': result.img['alt'], 'url': BASE_URL + result['href'], 'img': img, 'description': description}
            films_list.append(dict_films)
        return films_list

    def categories(self, url, category=None):
        html = self.send_request('GET', url)
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup.find_all('li', {'class': 'dropdown-submenu'})[0]
        tags.ul.unwrap()
        new_html = str(tags).replace('dropdown-submenu', '').replace('</a>\n', '</a> </li>')
        new_soup = BeautifulSoup(new_html, 'html.parser')
        new_tags = new_soup.find_all('li')
        category_list = []
        for info in new_tags:
            if category is not None:
                if category == info.text.replace('ç', 'c'):
                    category_dict = {'category': info.text, 'url': info.a['href']}
                    category_list.append(category_dict)
            else:
                category_dict = {'category': info.text, 'url': info.a['href']}
                category_list.append(category_dict)
        return category_list

    def get_description(self, url):
        html = self.send_request('GET', url)
        soup = BeautifulSoup(html, 'html.parser')
        try:
            tags = soup.find('div', {'id': 'content-main'})
            films = tags.find_all('div', {'itemprop': 'description'})
            if not films:
                result = 'Conteúdo sem descrição!!!'
                return result
            else:
                for info in films:
                    result = info.text.replace('\n', '')
                    return result
        except:
            return 'Conteúdo sem descrição!!!'

    def find_streams(self, url):
        self.url_server = URL_SERVER
        if 'tv' in url:
            self.is_tv = True
            self.url_server = URL_SERVER
        self.headers['referer'] = self.url_server
        html = self.send_request('GET', url, headers=self.headers)
        soup = BeautifulSoup(html, 'html.parser')
        player, stream = self.get_player_id(soup)
        try:
            tags = soup.find('div', {'id': 'content-main'})
            films = tags.find_all('div', {'itemprop': 'description'})
            if not films:
                result = {'desc': 'Conteúdo sem descrição!!!', 'player': player, 'stream': stream}
                return result
            else:
                for info in films:
                    result = {'desc': info.text.replace('\n', ''), 'player': player, 'stream': stream}
                    return result
        except ValueError:
            result = {'desc': None, 'player': None, 'stream': None}
            return result

    def get_player_id(self, iframe):
        try:
            url_player = iframe.find('div', {'id': 'video-wrapper'}).iframe['src']
            player, stream = self.get_player(url_player)
        except ValueError:
            player = None
            stream = None
        return player, stream

    def get_player(self, url):
        url_player = self.url_server + url
        self.response = self.send_request('GET', url_player, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            return url_player, self.decrypt_link(url_action, value)

    def decrypt_link(self, url, value):
        self.headers["referer"] = self.referer
        payload = {
            "data": value
        }
        self.response = self.send_request('POST', url, data=payload, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            return self.redirect_link(url_action, value)

    def redirect_link(self, url, value):
        self.headers["referer"] = self.referer
        payload = {
            "data": value
        }
        self.response = self.send_request('POST', url, data=payload, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            return self.get_ads_link(url_action, value)

    def get_ads_link(self, url, value):
        self.headers["referer"] = self.referer
        payload = {
            "data": value
        }
        self.response = self.send_request('POST', url, data=payload, headers=self.headers)
        if self.response:
            iframe = BeautifulSoup(self.response, 'html.parser').find('iframe')
            url_action = iframe['src']
            return self.get_stream(url + url_action.replace('./', '/'), url)

    def get_stream(self, url, referer):
        self.headers["referer"] = referer
        self.response = self.send_request('GET', url, headers=self.headers)
        if self.response:
            soup = BeautifulSoup(self.response, 'html.parser')
            if self.is_tv:
                return re.compile(r'source: "(.*?)",').findall(self.response)[0]
            return soup.find('div', {'id': 'instructions'}).source['src'].replace('\n', '').split('?')[0]

    def download(self, url):
        filename = url.split('/')[-1].replace('?attachment=true', '')
        print('Downloading...' + filename)
        with requests.get(url, stream=True) as r:
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

    def select_film(self, films, play=False):
        print('\n')
        for index, film in enumerate(films):
            print(str(index) + ' == ' + film['title'])
        print('\n')
        selected = input('Digite o número correspondente ao filme que deseja assistir: ')
        if selected.isalpha():
            print('\nOpção inválida, tente novamente!!!')
            time.sleep(3)
            return self.select_film(films)
        else:
            selected = int(selected)
        try:
            print(films[selected]['url'])
        except ValueError:
            print('Esse filme não existe')
            self.select_film(films)
        filme = films[selected]['url']
        title = films[selected]['title']
        img = films[selected]['img']
        description = films[selected]['description']
        video_url = None
        try:
            video_url = self.find_streams(filme)['stream']
        except ValueError:
            print('Desculpe não encontramos o link do filme escolhido,tente novamente inserindo o nome real do filme.')
            films = self.search()
            self.select_film(films)
        if len(self.devices) > 0 and video_url and play:
            print('\nOs seguintes dispositivos foram encontrados: ')
            for index, device in enumerate(self.devices):
                print(f'[x] {index} ==> {device}')
            action = input('\nSelecione um dispositivo de mídia inserindo'
                           ' o número correspondente para iniciar a transmissão: ')
            if action != '':
                cast = self.chromecasts[int(action)]
                cast.wait()
                mc = cast.media_controller
                mc.play_media(video_url, 'video/mp4')
                print(f'\nReproduzindo em {self.devices[int(action)]}\n')
                discovery.stop_discovery(self.browser)
                time.sleep(2)
            else:
                print('Nenhum dispositivo selecionado, iniciando no player padrão...\n')
                self.play(video_url, title, img, description)
        elif video_url and play:
            self.play(video_url, title, img, description)
        return

    def get_chromecasts(self):
        self.chromecasts, self.browser = get_chromecasts()
        self.devices = [cc.device.friendly_name for cc in self.chromecasts]

    def play(self, url, title=None, img=None, description=None):
        dict_details = {"url": url,
                        "title": title,
                        "img": img,
                        "description": description
                        }
        with open('player.html', 'w') as f:
            f.write(html_player % dict_details)
        simple_server = SimpleServerHttp()
        simple_server.start()
        webbrowser.open('http://localhost:9090/player.html')
        print('Starting video')
        time.sleep(5)
        simple_server.stop()
        return 'Exiting...'
