# -*- coding: utf-8 -*-
#
import re
import time
import shutil
import argparse
import webbrowser
import http.server
import socketserver
import threading
import requests
from redecanais.player import html_player
from bs4 import BeautifulSoup

BASE_URL = 'https://redecanais.pictures'


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
        if parameter:
            film_name = parameter
        else:
            film_name = input('Digite o nome do filme que deseja assistir: ')
        url_search = f'{BASE_URL}/search.php?keywords={film_name.replace(" ", "+")}&video-id='
        # print(url_search)
        return self.films_per_genre(url_search)

    def films(self, url, category, page=None):
        if type(category) is dict:
            list_category = ['legendado', 'dublado', 'nacional']
            if 'ficcao' in category['genre']:
                genre = category['genre'] + '-filmes'
            else:
                genre = category['genre'].capitalize() + '-Filmes'
            if category['category'] in list_category:
                info_category = self.categories(url, category['category'].capitalize() + ' ')[0]
                pages = re.compile(r'videos-(.*?)-date').findall(info_category['url'])[0]
                if category['category'] == 'dublado':
                    # print(BASE_URL + info_category['url'].replace('filmes-dublado', genre).replace(pages, str(category['page'])))
                    url_category_films = BASE_URL + info_category['url'].replace('filmes-dublado', genre).replace(pages, str(category['page']))
                    return self.films_per_genre(url_category_films)
                else:
                    # print(BASE_URL + info_category['url'].replace('filmes-' + category['category'], genre + '-' + category['category'].capitalize()).replace(pages, str(category['page'])))
                    url_category_films = BASE_URL + info_category['url'].replace('filmes-' + category['category'], genre + '-' + category['category'].capitalize()).replace(pages, str(category['page']))
                    return self.films_per_genre(url_category_films)
            else:
                info_category = self.categories(url, category['category'].capitalize() + ' ')[0]
                pages = re.compile(r'videos(.*?)date').findall(info_category['url'])[0]
                if page is not None:
                    url_category_films = BASE_URL + info_category['url'].replace(pages, '-' + str(page) + '-')
                else:
                    url_category_films = BASE_URL + info_category['url'].replace(pages, '-' + str(category['page']) + '-')
                # print(url_category_films)
                return self.films_per_category(url_category_films)
        else:
            info_category = self.categories(url, category.capitalize() + ' ')[0]
            pages = re.compile(r'videos(.*?)date').findall(info_category['url'])[0]
            if page is not None:
                url_category_films = BASE_URL + info_category['url'].replace(pages, '-' + str(page) + '-')
            else:
                url_category_films = BASE_URL + info_category['url'].replace(pages, str(category['page']))
            # print(url_category_films)
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
        url_player = iframe.find('div', {'id': 'video-wrapper'}).iframe['src']
        get_link = self.check_link(url_player)
        if get_link is not None:
            url_player.replace(BASE_URL, '')
            url_player_dict = {'embed': url_player, 'player': url_player}
        else:
            print('Algo deu errado, nenhum player de vídeo encontrado...')
            url_player_dict = {}
        # url_player_dict = {'embed': url_player, 'player': url_player.replace('.php', 'playerfree.php')}
        # url_player_dict = {'embed': url_player, 'player': url_player}
        return url_player_dict

    def check_link(self, url):
        for i in range(1, 10):
            split_link = url.split('?')
            player_link = f'{BASE_URL}/player{i}/serverf{i}.php?{split_link[1]}'
            test_url = requests.get(player_link)
            if test_url.status_code == 200:
                return player_link
            else:
                player_link.replace('.php', 'playerfree.php')
                test_url = requests.get(player_link)
                if test_url.status_code == 200:
                    return player_link

    def get_stream(self, url, referer):
        html = self.open(url, referer)
        #print(url)
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
        player_url = rede.get_player(filme)
        if 'cometa.top' in player_url:
            video_url = rede.get_stream(url=f"https://cometa.top{player_url['player']}", referer=f"https://cometa.top{player_url['embed']}")
        else:
            video_url = rede.get_stream(url=f"{BASE_URL}{player_url['player']}", referer=f"{BASE_URL}{player_url['embed']}")
        print(video_url)
        rede.play(video_url, title, img, description)
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
        webbrowser.open('http://localhost:9090/player.html')
        print('Starting video')
        time.sleep(3600)
        simple_server.stop()
        return


def check_host():
    test_url = requests.get(BASE_URL)
    if test_url.status_code == 200:
        return True
    else:
        return False


def _str_to_bool(s):
    if s.lower() not in ['true', 'false']:
        raise ValueError('Need bool; got %r' % s)
    return {'true': True, 'false': False}[s.lower()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', nargs='*', help='Use o link de um determinado filme para extrair informações...')
    parser.add_argument('-a', '--all', nargs='?', default=False, const=False, type=_str_to_bool, help='Use True ou False para extrair ou não todo conteúdo de uma determinada página...')
    parser.add_argument('-c', '--category', default=['dublado'], nargs='*', help='Use para definir uma categoria.')
    parser.add_argument('-g', '--genre', default=['acao'], nargs='*', help='Use para definir um gênero.')
    parser.add_argument('-p', '--page', default='1', type=int, nargs='*', help='Use para especificar uma página.')
    parser.add_argument('--host', nargs='*', help='Defina o host.')
    parser.add_argument('--stream', nargs='*', help='Use com um link embed para abrir o vídeo.')
    parser.add_argument('--search', nargs='?', help='Use para buscar filmes por título.')
    parser.add_argument('--select', nargs='?', default=False, const=False, type=_str_to_bool, help='Use True ou False para abrir o menu de seleçao dos filmes...')
    parser.add_argument('arg', nargs='*')
    parsed = parser.parse_args()
    return vars(parsed)


if __name__ == '__main__':
    args = main()

    if not check_host():
        if args['host']:
            BASE_URL = args['host'][0]

    rede = ChannelsNetwork()
    # categorias = rede.categories(BASE_URL + '/browse.html')
    # print(categorias)
    # filmes = rede.films(BASE_URL + '/browse.html', category='lancamentos', page=1)
    # search_film = rede.search()
    # print(search_film)
    # filmes = rede.films(BASE_URL, category={'category': 'dublado', 'genre': 'terror', 'page': 2})
    # link_test = 'https://redecanais.rocks/watch.php?vid=be4cbfff1'
    # player_url = rede.get_player(link_test)
    # player_url = rede.get_player('https://redecanais.rocks/dragon-ball-super-broly-dublado-2019-1080p_00f2e831c.html')
    # print(player_url)
    # video_url = rede.get_stream(url='https://cometa.top/player3/serverfplayerfree.php?vid=VNGDRSULTMTO4K', referer='https://cometa.top/player3/serverf.php?vid=VNGDRSULTMTO4K')
    # video_url = rede.get_stream(url=f"{BASE_URL}{player_url['player']}", referer=f"{BASE_URL}{player_url['embed']}")
    # print(video_url)
    # rede.download(video_url)
    # rede.play(video_url)
    # select_film = rede.select_film(filmes)

    parameters = {}
    if args['category']:
        parameters['category'] = args['category'][0]
    if args['genre']:
        parameters['genre'] = args['genre'][0]
    if args['page']:
        parameters['page'] = args['page']
    if args['stream']:
        link_stream = args['stream']

    filmes = rede.films(BASE_URL, category=parameters)

    if args['url']:
        player_url = rede.get_player(args['url'][0])
        video_url = rede.get_stream(url=f"{BASE_URL}{player_url['player']}", referer=f"{BASE_URL}{player_url['embed']}")
        rede.play(video_url)
    if args['all']:
        print(filmes)
    if args['select']:
        rede.select_film(filmes)
    if args['search']:
        print(rede.search(args['search']))
    else:
        print(rede.search())