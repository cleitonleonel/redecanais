O **redecanais** ajuda você a assistir vários filmes via linha de comando com *facilidade*:

.. código:: python

    """Modo Simples.

    Uso:
      redecanais.py --url <name>...
      redecanais.py --all <name>... 
      redecanais.py --category <name>...
      redecanais.py --genre <name>...
      redecanais.py --page <name>...
      redecanais.py --host <name>...                             
      redecanais.py --stream <name>...
      redecanais.py --search <name>...
      redecanais.py --select <name>...
      redecanais.py (-h | --help)
      redecanais.py --version

    Opções:
    '-u', '--url', help='Use o link de uma determinada página para extrair informações...'
    '-a', '--all', help='Use True ou False para extrair ou não todo conteúdo de uma determinada página...'
    '-c', '--category', help='Use para definir uma categoria.'
    '-g', '--genre', help='Use para definir um gênero.'
    '-p', '--page', help='Use para especificar uma página.'
    '--host', help='Defina o host.'
    '--stream', help='Use com um link embed para abrir o vídeo.'
    '--search', help='Use para buscar filmes por título.'
    '--select', help='Use True ou False para abrir o menu de seleçao dos filmes...'

    Recomendado:
    'python redecanais --page 2 --all True --select True'

    """
    
    from redecanais.redecanais import ChannelsNetwork


    if __name__ == '__main__':
        args = main()
        print(arguments)