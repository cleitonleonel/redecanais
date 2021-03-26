# -*- coding: utf-8 -*-
#
import os
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
from redecanais.settings import URL_SERVER, URL_TV_SERVER
from sys import platform as _sys_platform
from redecanais.player import html_player
from bs4 import BeautifulSoup
from numpy import interp

PATH_PLAYER_VLC = None
PATH_PLAYER_FF = None
PLAYER_COMMAND = ''


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


def progressbar(it, prefix="", size=60, file=sys.stdout):
    count = len(it)

    def show(j):
        x = int(size * j / count)
        file.write("%s[%s%s] %i/%i\r" % (prefix, "#" * x, "." * (size - x), j, count))
        file.flush()

    show(0)
    for i, item in enumerate(it):
        yield item
        show(i + 1)
    file.write("\n")
    file.flush()


class Progress(object):
    def __init__(self, value, end, title='Downloading', buffer=20):
        self.title = title
        self.end = end - 1
        self.buffer = buffer
        self.value = value
        self.progress()

    def progress(self):
        maped = int(interp(self.value, [0, self.end], [0, self.buffer]))

        print(
            f'{self.title}: [{"#" * maped}{"-" * (self.buffer - maped)}]{self.value}/'
            f'{self.end} {((self.value / self.end) * 100):.2f}%', end='\r\n\r'
        )


platform = _get_platform()
if platform == 'linux':
    player = os.popen('which vlc').read()
    if player != '':
        PATH_PLAYER_VLC = 'cvlc '
    else:
        print('Instale o ffmpeg ou player vlc')
        # PATH_PLAYER_FF = 'redecanais/src/linux/bin/ffplay'

elif platform == 'windows':
    player = os.popen('vlc').read()
    if player != '':
        PATH_PLAYER_VLC = r'\\progra~1\\videolan\\vlc'
    else:
        print('Instale o ffmpeg ou player vlc')
        # PATH_PLAYER_FF = 'redecanais/src/windows/bin/ffplay.exe'

print(f'Sistema Operacional {platform} suportado!!!\n')


class ProxyRequests(object):
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


class SimpleServerHttp(object):
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

    @staticmethod
    def headers():
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
        self.progress = Progress
        self.is_tv = False
        self.devices = []
        self.chromecasts = None
        self.browser = None
        self.url_server = None
        self.stream_ref = None
        self.external_player = None
        self.web_player_disable = False
        self.chromecast_ip = None
        self.headers = self.headers()
        super().__init__()

    def search(self, parameter=None, description=True):
        if type(parameter) is list:
            film_name = ' '.join(parameter).capitalize()
        elif parameter != '' and type(parameter) is str:
            film_name = parameter.capitalize()
        else:
            film_name = input('Digite o nome do filme que deseja assistir: ')
        data = {"queryString": film_name}
        url_search = f'{self.url_server}/ajax_search.php'

        if self.debug:
            print('Search: ', url_search)
        return self.search_films(url_search, data, description=description)

    def get_links_categories(self, url, category):
        info_category = self.categories(url, category['category'].capitalize() + ' ')[0]
        html = self.send_request('GET', self.url_server + info_category['url'])
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
                    url_category_films = self.url_server + item.replace(pages, str(category['page']))
                    return self.films_per_category(url_category_films)
        else:
            info_category = self.categories(url, category.capitalize() + ' ')[0]
            pages = re.compile(r'videos(.*?)date').findall(info_category['url'])[0]
            if page is not None:
                url_category_films = self.url_server + info_category['url'].replace(pages, '-' + str(page) + '-')
            else:
                url_category_films = self.url_server + info_category['url'].replace(pages, str(category['page']))
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
                    img = self.url_server + result.img['data-echo']
                else:
                    img = result.img['data-echo']
                description = self.get_description(self.url_server + result['href'])
                dict_films = {'title': result.img['alt'], 'url': self.url_server + result['href'], 'img': img, 'description': description}
                films_list.append(dict_films)
            return films_list
        except ValueError:
            info_warning = soup.find('div', {'class': 'col-md-12 text-center'}).text
            print(info_warning)
            sys.exit()

    def search_films(self, url, data, description=None):
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
                    description = self.get_description(self.url_server + result['href'])
                else:
                    description = None
                dict_films = {'title': result.text, 'url': self.url_server + result['href'], 'img': '', 'description': description}
                films_list.append(dict_films)
            else:
                result = info.a
                dict_films = {'title': result.text, 'url': self.url_server + result['href'], 'img': '', 'description': ''}
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
                img = self.url_server + result.img['data-echo']
            else:
                img = result.img['data-echo']
            description = self.get_description(self.url_server + result['href'])
            dict_films = {'title': result.img['alt'], 'url': self.url_server + result['href'], 'img': img, 'description': description}
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
        self.progress(35, 99, 'Aguade um instante...')
        self.url_server = URL_SERVER
        if 'tv' in url:
            self.is_tv = True
            self.url_server = URL_TV_SERVER
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
        self.progress(40, 99, 'Aguade um instante...')
        try:
            url_player = iframe.find('div', {'id': 'video-wrapper'}).iframe['src']
            player, stream = self.get_player(url_player)
        except ValueError:
            player = None
            stream = None
        return player, stream

    def get_player(self, url):
        self.progress(50, 99, 'Aguade um instante...')
        url_player = self.url_server + url
        self.response = self.send_request('GET', url_player, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            return url_player, self.decrypt_link(url_action, value)

    def decrypt_link(self, url, value):
        self.progress(55, 99, 'Aguade um instante...')
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
        self.progress(65, 99, 'Aguade um instante...')
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
        self.progress(70, 99, 'Stream encontrado...')
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
        self.progress(75, 99, 'Resolvendo stream...')
        self.stream_ref = referer
        self.headers["referer"] = self.referer
        self.response = self.send_request('GET', url, headers=self.headers)
        if self.response:
            soup = BeautifulSoup(self.response, 'html.parser')
            if self.is_tv:
                return re.compile(r'source: "(.*?)",').findall(self.response)[0]
            return soup.find('div', {'id': 'instructions'}).source['src'].replace('\n', '').split('?')[0]

    def download(self, url):
        filename = url.split('/')[-1].replace('?attachment=true', '')
        print('Downloading...' + filename)
        with requests.get(url, headers=self.headers, stream=True) as r:
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

    def check_link(self, url):
        self.headers["referer"] = self.stream_ref
        referred = False
        with_referer = None
        without_referer = None
        try:
            with_referer = self.session.request('GET', url, headers=self.headers, stream=True)
            without_referer = self.session.request('GET', url, stream=True)
        except:
            print('\nServidor offline ou link quebrado, tente novamente mais tarde!!!\n')
        if with_referer:
            # print('Link com referer, tentando abrir com ffmpeg.')
            self.web_player_disable = True
            referred = True
            return referred, True
        elif without_referer:
            return referred, True
        return referred, False

    def select_film(self, films, play=False):
        print('\n')
        for index, film in enumerate(films):
            print(str(index) + ' == ' + film['title'])
        print('\n')
        selected = input('Digite o número correspondente ao filme que deseja assistir: ')
        self.progress(1, 99, 'Aguade um instante...')
        if selected.isalpha():
            self.progress(67, 99, 'Concluindo Busca.')
            self.progress(99, 99, 'Busca encerrada')
            print('\nOpção inválida, tente novamente!!!')
            return self.select_film(films)
        else:
            selected = int(selected)
        try:
            self.progress(10, 99, 'Aguade um instante...')
            # print(f'\n{films[selected]["url"]}')
        except ValueError:
            self.progress(67, 99, 'Concluindo Busca.')
            self.progress(99, 99, 'Busca encerrada')
            print('Esse filme não existe')
            self.select_film(films)
        filme = films[selected]['url']
        title = films[selected]['title']
        img = films[selected]['img']
        description = films[selected]['description']
        video_url = None
        is_valid = False
        self.progress(30, 99, 'Aguade um instante...')
        try:
            video_url = self.find_streams(filme)['stream']
            is_referred, is_valid = self.check_link(video_url)
            if is_valid and is_referred and self.external_player:
                self.progress(99, 99, 'Starting vídeo stream')
                print('\nIniciando player, aguarde...')
                if PATH_PLAYER_FF:
                    os.system(f'{PATH_PLAYER_FF} -headers "Referer: {self.stream_ref}" -i {video_url} > /dev/null 2>&1 &')
                    sys.exit(0)
                elif PATH_PLAYER_VLC:
                    # os.system(f'{PATH_PLAYER_VLC} --http-referrer "{self.stream_ref}" {video_url} > /dev/null 2>&1 &')
                    chromecast_command = ''
                    if self.chromecast_ip:
                        chromecast_command = f'--sout "#chromecast" --sout-chromecast-ip={self.chromecast_ip} --demux-filter=demux_chromecast'
                        os.system(f'{PATH_PLAYER_VLC} --http-referrer "{self.stream_ref}" {video_url} {chromecast_command} > /dev/null 2>&1 &')
                        sys.exit(0)
                    else:
                        os.system(f'vlc --http-referrer "{self.stream_ref}" {video_url} > /dev/null 2>&1 &')
                        sys.exit(0)
            elif not is_referred and video_url:
                pass
        except ValueError:
            print('Desculpe não encontramos o link do filme escolhido,tente novamente inserindo o nome real do filme.')
            films = self.search()
            self.select_film(films)
        if is_valid and self.web_player_disable and len(self.devices) > 0 and video_url and play:
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
                self.progress(99, 99, 'Starting vídeo stream')
                print(f'\nReproduzindo em {self.devices[int(action)]}\n')
                discovery.stop_discovery(self.browser)
                time.sleep(2)
            else:
                print('Nenhum dispositivo selecionado, iniciando no player padrão...\n')
                self.play(video_url, title, img, description)
        elif is_valid and video_url and play:
            self.progress(99, 99, 'Starting vídeo stream')
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
