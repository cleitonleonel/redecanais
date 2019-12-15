from __future__ import absolute_import

import os
import sys

if __package__ == '':
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

from redecanais.redecanais import *


if __name__ == '__main__':
    args = main()

    if not check_host():
        if args.host:
            BASE_URL = args.host[0]

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
    if args.category:
        parameters['category'] = args.category[0]
    if args.genre:
        parameters['genre'] = args.genre[0]
    if args.page:
        parameters['page'] = args.page[0]
    if args.stream:
        link_stream = args.stream

    filmes = rede.films(BASE_URL, category=parameters)

    if args.url:
        player_url = rede.get_player(args.url[0])
        video_url = rede.get_stream(url=f"{BASE_URL}{player_url['player']}", referer=f"{BASE_URL}{player_url['embed']}")
        rede.play(video_url)
    if args.all:
        print(filmes)
    if args.select:
        rede.select_film(filmes)
    if args.search:
        print(rede.search(args.search))
    else:
        if args.select:
            rede.select_film(filmes)
        else:
            print(rede.search())
