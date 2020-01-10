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
from redecanais.settings import URL_SERVER
from sys import platform as _sys_platform
from redecanais.player import html_player
from bs4 import BeautifulSoup

BASE_URL = URL_SERVER


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
        self.server.socket.close()
        self.server.shutdown()
        # self.server.server_close()


class Browser:

    def __init__(self):
        self.request = None
        self.response = None

    def headers(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        }
        return headers

    def open(self, url, referer=None):
        if referer:
            headers = self.headers()
            headers['referer'] = referer
        else:
            headers = self.headers()
        with requests.session() as s:
            self.request = s.get(url, headers=headers)
            self.response = self.request.text
        return self.response


class ChannelsNetwork(Browser):

    def __init__(self):
        super().__init__()

    def search(self, parameter=None):
        if isinstance(parameter, list):
            parameter = ' '.join([str(elem) for elem in parameter])
        if parameter:
            film_name = parameter
        else:
            film_name = input('Digite o nome do filme que deseja assistir: ')

            if film_name.isalpha():
                if film_name.lower() == 's' or film_name.lower() == 'sair' or film_name.lower() == 'restart' or film_name.lower() == 'exit':
                    sys.exit()
        url_search = f'{BASE_URL}/search.php?keywords={film_name.replace(" ", "+")}&video-id='
        return self.films_per_genre(url_search)

    def films(self, url, category, page=None):
        if type(category) is dict:
            list_category = ['legendado', 'dublado', 'nacional']
            if category['category'] in list_category:
                info_category = self.categories(url, category['category'].capitalize() + ' ')[0]
                pages = re.compile(r'videos-(.*?)-date').findall(info_category['url'])[0]
                if category['category'] == 'dublado':
                    if 'ficcao' in category['genre']:
                        genre = category['genre'] + '-cientifica-filmes'
                    else:
                        genre = category['genre'].capitalize() + '-Filmes'
                    url_category_films = BASE_URL + info_category['url'].replace('filmes-dublado', genre).replace(pages, str(category['page']))
                    print(url_category_films)
                    return self.films_per_genre(url_category_films)
                if category['category'] == 'nacional':
                    if 'ficcao' in category['genre']:
                        genre = category['genre'] + '-cientifica-filmes'
                    else:
                        genre = category['genre'] + '-filmes'
                    url_category_films = BASE_URL + info_category['url'].replace('filmes-' + category['category'], genre + '-' + category['category']).replace(pages, str(category['page']))
                    print(url_category_films)
                    return self.films_per_genre(url_category_films)
                else:
                    if 'ficcao' in category['genre']:
                        genre = category['genre'].capitalize() + '-Cientifica-Filmes'
                    else:
                        genre = category['genre'].capitalize() + '-Filmes'
                    url_category_films = BASE_URL + info_category['url'].replace('filmes-' + category['category'], genre + '-' + category['category'].capitalize()).replace(pages, str(category['page']))
                    print(url_category_films)
                    return self.films_per_genre(url_category_films)
            else:
                info_category = self.categories(url, category['category'].capitalize() + ' ')[0]
                pages = re.compile(r'videos(.*?)date').findall(info_category['url'])[0]
                if page is not None:
                    url_category_films = BASE_URL + info_category['url'].replace(pages, '-' + str(page) + '-')
                else:
                    url_category_films = BASE_URL + info_category['url'].replace(pages, '-' + str(category['page']) + '-')
                print(url_category_films)
                return self.films_per_category(url_category_films)
        else:
            info_category = self.categories(url, category.capitalize() + ' ')[0]
            pages = re.compile(r'videos(.*?)date').findall(info_category['url'])[0]
            if page is not None:
                url_category_films = BASE_URL + info_category['url'].replace(pages, '-' + str(page) + '-')
            else:
                url_category_films = BASE_URL + info_category['url'].replace(pages, str(category['page']))
            print(url_category_films)
            return self.films_per_category(url_category_films)

    def films_per_category(self, url):
        html = self.open(url)
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

    def films_per_genre(self, url, category=None, genre=None):
        url_genre = url
        html = self.open(url_genre)
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
        # print(url)
        html = self.open(url)
        # print(html)
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup.find_all('li', {'class': 'dropdown-submenu'})[0]
        # print(tags)
        tags.ul.unwrap()
        new_html = str(tags).replace('dropdown-submenu', '').replace('</a>\n', '</a> </li>')
        new_soup = BeautifulSoup(new_html, 'html.parser')
        new_tags = new_soup.find_all('li')
        # print(new_tags)
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
        html = self.open(url)
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

    def get_player(self, url):
        html = self.open(url)
        iframe = BeautifulSoup(html, 'html.parser')
        url_src = iframe.find('div', {'id': 'video-wrapper'}).iframe['src']
        get_link = self.resolve_link(url_src)
        if get_link is not None:
            url_player = get_link.replace(BASE_URL, '')
            url_player_dict = {'embed': url_player, 'player': url_player}
        else:
            print('Algo deu errado, nenhum player de vídeo encontrado...')
            url_player_dict = {}
        # url_player_dict = {'embed': url_player, 'player': url_player.replace('.php', 'playerfree.php')}
        # url_player_dict = {'embed': url_player, 'player': url_player}
        return url_player_dict

    def resolve_link(self, url):
        links = self.generate_link(url)
        for player_link in links:
            status = self.check_link(player_link)
            if status:
                return player_link

    def generate_link(self, url):
        split_link = url.split('?')
        list_links = []
        for i in range(1, 10):
            player_link1 = f'{BASE_URL}/player{i}/serverf{i}.php?{split_link[1]}'
            list_links.append(player_link1)
            player_link2 = f'{BASE_URL}/player{i}/serverf{i}player.php?{split_link[1]}'
            list_links.append(player_link2)
            player_link3 = f'{BASE_URL}/player{i}/serverf{i}playerfree.php?{split_link[1]}'
            list_links.append(player_link3)
        return list_links

    def check_link(self, url):
        test_url = requests.get(url)
        if test_url.status_code == 200:
            html = self.open(url, referer=url)
            source = BeautifulSoup(html, 'html.parser')
            try:
                url_stream = source.find('div', {'id': 'instructions'}).source['src']
                return True
            except:
                pass
        else:
            return False

    def get_stream(self, url, referer):
        html = self.open(url, referer)
        source = BeautifulSoup(html, 'html.parser')
        url_stream = source.find('div', {'id': 'instructions'}).source['src']
        return url_stream

    def download(self, url):
        filename = url.split('/')[-1].replace('?attachment=true', '')
        print('Downloading...' + filename)
        with requests.get(url, stream=True) as r:
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

    def select_film(self, films):
        print('\n')
        for index, film in enumerate(films):
            print(str(index) + ' == ' + film['title'])
        print('\n')
        selected = input('Digite o número correspondente ao filme que deseja assistir: ')
        if selected.isalpha():
            if selected.lower() == 's' or selected.lower() == 'sair' or selected.lower() == 'restart':
                sys.exit()
            print('\nOpção inválida, tente novamente!!!')
            time.sleep(3)
            return self.select_film(films)
        else:
            selected = int(selected)
        print(films[selected]['url'])
        filme = films[selected]['url']
        title = films[selected]['title']
        img = films[selected]['img']
        description = films[selected]['description']
        player_url = self.get_player(filme)
        if 'cometa.top' in player_url:
            video_url = self.get_stream(url=f"https://cometa.top{player_url['player']}", referer=f"https://cometa.top{player_url['embed']}")
        else:
            video_url = self.get_stream(url=f"{BASE_URL}{player_url['player']}", referer=f"{BASE_URL}{player_url['embed']}")
        self.play(video_url, title, img, description)
        return

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
        platform = _get_platform()
        url = 'http://localhost:9090/player.html'
        webbrowser.open(url)
        print('Starting video')
        time.sleep(10)
        simple_server.stop()
        return 'Exiting...'


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
