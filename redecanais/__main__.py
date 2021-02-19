from __future__ import absolute_import
import os
import argparse
from redecanais.redecanais import *
from redecanais.version import __version_info__, __author_info__, __email__info__

BASE_DIR = os.getcwd()


if __package__ == '':
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)


def _str_to_bool(s):
    if s.lower() not in ['true', 'false']:
        raise ValueError('Need bool; got %r' % s)
    return {'true': True, 'false': False}[s.lower()]


def set_new_server(host):
    filename = BASE_DIR + '/redecanais/settings.py'

    if not os.path.exists(filename):
        os.mkdir(BASE_DIR + '/redecanais')
        with open(filename, 'w') as file:
            file.write("URL_SERVER = ''")

    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if 'URL_SERVER' in line:
                line = line.replace(line.split('=')[1], ' ' + "'" + host + "'")

    with open(filename, 'w') as file:
        file.write(line)


def check_host():
    try:
        test_url = requests.get(BASE_URL)
        if test_url.status_code == 200:
            return True
        else:
            return False
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser(prog='redecanais')
    parser.add_argument('-v', '--version', action='version', version="{prog}s ({version})".format(prog="%(prog)", version=__version_info__ + ' Contato: ' + __email__info__), help='Obtenha informações da versão instalada.')
    parser.add_argument('-u', '--url', nargs='*', help='Use o link de uma determinada página para extrair informações...')
    parser.add_argument('-a', '--all', nargs='*', help='Use True ou False para extrair ou não todo conteúdo de uma determinada página...')
    parser.add_argument('-c', '--category', default=['dublado'], nargs='*', help='Use para definir uma categoria.')
    parser.add_argument('-g', '--genre', default=['acao'], nargs='*', help='Use para definir um gênero.')
    parser.add_argument('-p', '--page', default=['1'], type=int, nargs='*', help='Use para especificar uma página.')
    parser.add_argument('--host', nargs='*', help='Defina o host.')
    parser.add_argument('--stream', nargs='*', help='Use com um link embed para abrir o vídeo.')
    parser.add_argument('--search', nargs='*', help='Use para buscar filmes por título.')
    parser.add_argument('--select', nargs='*', help='Use True ou False para abrir o menu de seleçao dos filmes...')
    parser.add_argument('arg', nargs='*')
    parsed = parser.parse_args()
    return parsed


if __name__ == '__main__':

    args = main()

    rede = ChannelsNetwork()
    rede.get_chromecasts()

    parameters = {}

    if args.host:
        if not check_host():
            set_new_server(args.host[0])
            sys.exit()
        else:
            set_new_server(args.host[0])
            sys.exit()

    if args.category:
        parameters['category'] = args.category[0]
    if args.genre:
        parameters['genre'] = args.genre[0]
    if args.page:
        parameters['page'] = args.page[0]
    if args.stream:
        if args.stream[0].endswith('.html'):
            video_url = rede.find_streams(args.stream[0])
            rede.play(video_url)
        else:
            rede.play(args.stream[0])

    filmes = rede.films(BASE_URL, category=parameters)

    if args.url:
        info_film = rede.films_per_genre(args.url[0])
        print(info_film)
    if args.all:
        print(filmes)
    if args.select:
        rede.select_film(filmes, play=True)
    if args.search:
        filmes = rede.search(parameter=args.search)
        rede.select_film(filmes, play=True)
    else:
        if args.select != 'None':
            rede.select_film(filmes, play=True)
        else:
            filmes = rede.search()
            print(filmes)
            rede.select_film(filmes, play=True)
