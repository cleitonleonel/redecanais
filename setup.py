from distutils.core import setup
from setuptools import find_packages
setup(
  name='redecanais',
  packages=find_packages(),
  version='0.10',
  license='MIT',
  description='Busque,selecione e assista filmes do site https://www.redecanais.com a partir do prompt de comando.',
  author='Cleiton Leonel Creton',
  author_email='cleiton.leonel@gmail.com',
  url='https://github.com/cleitonleonel/redecanais.git',
  download_url='https://github.com/cleitonleonel/redecanais/archive/v_01.tar.gz',
  keywords=['SOME', 'MEANINGFULL', 'KEYWORDS'],
  install_requires=[
          'requests',
          'beautifulsoup4',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)
