O **redecanais** ajuda você a assistir vários filmes via linha de comando com *facilidade*:

# Instalação:
```shell script
pip install redecanais ou pip install git+https://github.com/cleitonleonel/redecanais.git
```

# Uso dentro do módulo:
```shell script
python redecanais.py --url <name>...
python redecanais.py --all <name>... 
python redecanais.py --category <name>...
python redecanais.py --genre <name>...
python redecanais.py --page <name>...
python redecanais.py --host <name>...                             
python redecanais.py --stream <name>...
python redecanais.py --search <name>...
python redecanais.py --select <name>...
python redecanais.py --external-player <name>...
python redecanais.py --renderer-ip <name>...
python redecanais.py (-h | --help)
python redecanais.py --version
```      

# Opções:
    
```shell script
python -m redecanais <options>

'-u', '--url', help='Use o link de uma determinada página para extrair informações...'
'-a', '--all', help='Use True ou False para extrair ou não todo conteúdo de uma determinada página...'
'-c', '--category', help='Use para definir uma categoria.'
'-g', '--genre', help='Use para definir um gênero.'
'-p', '--page', help='Use para especificar uma página.'
'--host', help='Defina o host.'
'--stream', help='Use com um link embed para abrir o vídeo.'
'--tv-channels', help='Use para definir o uso de canais de tv.'
'--search', help='Use para buscar filmes por título.'
'--select', help='Use True ou False para abrir o menu de seleçao dos filmes...'
'--external-player', help='Use para definir o uso de um player externo.'
'--renderer-ip', help='Use para definir o IP do dispositivo chromecast.'
```

# Recomendado:

```shell script
python -m redecanais --page 2 --all --select

python -m redecanais --search batman --select

python -m redecanais -g terror -c dublado --page 1 --select

python -m redecanais -g terror -c dublado --page 1 --select --external-player

python -m redecanais -g terror -c dublado --page 1 --select --external-player --renderer-ip 10.0.0.2

python -m redecanais -tv --search globo --select --external-player vlc --renderer-ip 10.0.0.2
```


# Importando o módulo:
```python
from redecanais.settings import URL_SERVER, URL_TV_SERVER
from redecanais.redecanais import ChannelsNetwork


if __name__ == '__main__':
    cn = ChannelsNetwork()
    cn.url_server = URL_SERVER
    films = cn.search('batman')
    print(films)
    #  cn.url_server = URL_TV_SERVER
    #  channels = cn.search('fox')
    #  cn.select_film(channels, play=True)
    cn.select_film(films, play=True)

```