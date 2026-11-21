# Créditos

## Motor de coleta: google-maps-scraper (gosom)

Este kit **não contém o código-fonte** do google-maps-scraper. Ele usa a imagem Docker
oficial publicada pelo autor (`gosom/google-maps-scraper`) e acrescenta, por cima, uma
camada própria (scripts, textos, relatório e documentação em português do Brasil).

- Autor: Georgios Komninos (@gosom)
- Projeto: https://github.com/gosom/google-maps-scraper
- Licença: MIT
- Imagem Docker: `gosom/google-maps-scraper`

Se este kit for útil para você, apoie o projeto original: dê uma estrela no repositório
acima. Sem o trabalho do autor, nada disso existiria.

### Aviso de licença MIT do projeto original

Reproduzido aqui conforme exige a licença:

```
MIT License

Copyright (c) 2023 Georgios Komninos

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Mapa do relatório

- **MapLibre GL JS** 5.24.1 (código aberto, licença BSD-3-Clause, © MapLibre contributors), embutida no
  relatório a partir de `scripts/vendor/maplibre/` sem alterações. Licença completa em
  `scripts/vendor/maplibre/LICENSE.txt`.
- **OpenFreeMap** (openfreemap.org) fornece o fundo do mapa, gratuitamente e sem chave. Atribuição exigida
  (aparece no canto do mapa e deve aparecer também em vídeos e materiais impressos):
  OpenFreeMap · © OpenMapTiles · Dados do © OpenStreetMap (openstreetmap.org/copyright).

## Tipografia

- **Inter** (© The Inter Project Authors, SIL Open Font License 1.1), pesos 400–700, subconjunto latin,
  embutida nas páginas a partir de `scripts/vendor/inter/` (pacote `@fontsource/inter@5.3.0`, sem alterações).
  Licença em `scripts/vendor/inter/LICENSE.txt`. Por estar embutida, nenhuma página do kit chama o Google Fonts.

## Sobre este repositório

A camada brasileira (tudo fora da imagem do gosom) é de Felipe Martins Muniz, licenciada
sob MIT (veja `LICENSE`).

## Outros kits consultados como referência de ideias

Antes de desenhar este kit, li como outros projetos organizam skill e comandos para o
mesmo motor, apenas para entender o problema. Nenhum texto, código, nome ou visual foi
copiado deles:

- https://github.com/Mahanaicoach/google-maps-scraper-kit
- https://github.com/vzbaggio/google-maps-scraper-kit
