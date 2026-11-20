# Pacotes de marca

Um pacote é uma pasta `brands/<nome>/` com um `brand.py`. Só `brands/demo/` vai para o git: os outros ficam na sua máquina
(ou num repositório privado seu, apontado por `brands_dir` no `config.local.json`).

Para um cliente novo: copie `brands/demo/`, troque o que o cliente precisa, e ponha `"brand": "<nome>"` no
`config.local.json`. Se precisou editar `lib/` para trocar de cliente, sobrou cliente dentro do núcleo.

| nome | padrão | o quê |
|---|---|---|
| `ACCENT` | `#52B8FF` | a ÚNICA cor de destaque |
| `INK` | `#0E1116` | a superfície mais escura |
| `PAPER` | `#F4F1EA` | a superfície mais clara |
| `MUTED` | `#737882` | texto secundário |
| `FONT_DISPLAY` | `Arial-BoldMT` | nome PostScript da fonte de título (o padrão de `text()`) |
| `FONT_BODY` | `ArialMT` | nome PostScript da fonte de corpo |
| `FONT_FILES` | Arial do Windows | `{nome PostScript: caminho do .ttf/.otf}`: o arquivo usado para medir e desenhar o preview |

O nome PostScript tem que ser o mesmo que o Photoshop e o Illustrator enxergam, e a fonte tem que estar instalada no sistema.
O arquivo em `FONT_FILES` tem que ser dessa mesma fonte, senão a medida do preview não é a do app.

As cenas do cliente também moram no pacote (`brands/<nome>/thumb_ep12.py`, por exemplo), nunca em `lib/` ou `test/`.
