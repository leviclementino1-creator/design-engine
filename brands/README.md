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

## ESTILO.md

`brand.py` guarda os valores; `ESTILO.md` guarda o que os valores não dizem: composição, tom, o que é fixo e o que varia, o
que nunca fazer, o que já foi reprovado. É o que o Claude lê no começo de toda sessão do cliente. O gabarito é
`brands/demo/ESTILO.md`, e o método para preenchê-lo a partir das peças, dos projetos e do manual do cliente está em
`skill/design-engine/references/cliente.md`.

O material do cliente (peças de exemplo, `.psd`, `.ai`, fontes, manual) também mora no pacote, por exemplo em
`brands/<nome>/referencias/`. Fica fora do git como o resto.

As cenas do cliente também moram no pacote (`brands/<nome>/thumb_ep12.py`, por exemplo), nunca em `lib/` ou `test/`.
