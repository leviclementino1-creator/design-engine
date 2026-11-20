# API

```python
import sys; sys.path.insert(0, r"<repo>/lib")
from engine import Doc, ACCENT, INK, PAPER, MUTED, WHITE, BLACK, fit_size, wrap, measure, layout, Overflow
```

## Convenções

- **Coordenadas** em pixels, origem no canto superior esquerdo, y para baixo. `box` é `(x, y, largura, altura)`.
- **Ordem**: as camadas são criadas de baixo para cima. A primeira que você escreve fica no fundo.
- **Cores**: `"#RRGGBB"` ou `[r, g, b]` de 0 a 1. `ACCENT`, `INK`, `PAPER` e `MUTED` vêm do pacote de marca ativo.
- **Texto** é ancorado na **linha de base**: `pos` é o começo da linha de base (`align="left"`), o meio (`"center"`) ou o fim
  (`"right"`). Não é o canto da caixa.
- **Fontes** pelo nome PostScript (`"Arial-BoldMT"`), que é o que o Photoshop e o Illustrator pedem. O arquivo usado para medir
  e desenhar o preview vem de `FONT_FILES` no pacote de marca.
- **Nomes** de camada vão para dentro do app: escreva nomes que outro designer entenda.

## Doc

```python
d = Doc(nome, largura, altura, bg=None)      # bg = uma camada "BG" do tamanho do documento
```

| método | o que cria |
|---|---|
| `d.rect(nome, box, fill=None, radius=0, stroke=None, stroke_w=0, opacity=100)` | retângulo, cantos arredondados com `radius` |
| `d.ellipse(nome, box, fill=None, stroke=None, stroke_w=0, opacity=100)` | elipse inscrita na `box` |
| `d.line(nome, p1, p2, stroke, stroke_w=4, opacity=100)` | linha reta, pontas retas |
| `d.path(nome, pontos, fill=None, stroke=None, stroke_w=0, opacity=100)` | polígono fechado de lados retos (3+ pontos) |
| `d.text(nome, texto, pos, size=48, font=None, fill=None, align="left", tracking=0, leading=None, max_w=None, opacity=100)` | texto de ponto; `\n` quebra linha |
| `d.image(nome, caminho, box, fit="stretch", opacity=100)` | arquivo colocado; `fit="contain"` mantém a proporção e centraliza |
| `with d.group(nome, opacity=100):` | grupo; tudo criado dentro do `with` entra nele (pode aninhar) |
| `d.save(caminho)` | grava o IR (`.ir.json`) |
| `d.ir()` | o IR como dicionário |

Detalhes:

- O contorno (`stroke`) é **centrado** na borda da forma, nos três players.
- `tracking` é em milésimos de em, como nos apps. Entra **entre** os glifos: uma palavra com tracking alinhada à direita
  termina exatamente na âncora.
- `leading` é a distância em px entre linhas de base (padrão: 1,2 × `size`).
- `max_w` é a largura que o texto prometeu caber. Mais largo que isso levanta `Overflow` na hora, com os números.
- No Photoshop a linha vira um polígono preenchido da largura do traço (um caminho aberto não vira shape layer). No
  Illustrator é uma linha com traço de verdade.

## Medir e encaixar texto

| função | devolve |
|---|---|
| `measure(texto, font=None, size=48, tracking=0)` | largura em px de UMA linha, com kerning e tracking |
| `layout(texto, font=None, size=48, tracking=0)` | `([x de cada glifo], largura)` |
| `fit_size(texto, max_w, font=None, hi=400, lo=8, tracking=0)` | o maior tamanho inteiro em que a linha mais larga cabe |
| `wrap(texto, max_w, font=None, size=48, tracking=0)` | o texto com `\n`, quebrado por palavra |

`fit_size` e `wrap` levantam `Overflow` quando não tem como caber (uma palavra sozinha maior que a largura, por exemplo).

## Recusas (o motor para antes de mandar qualquer coisa para o app)

`ValueError`: cor que não é `#RRGGBB` nem três valores de 0 a 1, forma sem preenchimento e sem contorno, contorno sem
`stroke_w`, `box` sem área, `radius` maior que metade do lado menor, linha com dois pontos iguais, polígono com menos de 3
pontos, texto vazio, imagem que não existe, grupo vazio, documento sem camada, `opacity` fora de 0 a 100, fonte sem arquivo
em `FONT_FILES`.

## Build

```
python lib/build.py cena.ir.json --app ps|ai [--sheet folha.jpg] [--close]
```

Saída: o log do app (versão, árvore de camadas, `WARN`), depois `ORDER OK` e `PARITY 99.6% (OK)`. Código de saída 0 só quando
a ordem bate e a paridade passa de 97%. `--sheet` grava preview | app | diferença. `--close` fecha, sem salvar, o documento
que **este** build criou (é o que os testes usam); sem ele o documento fica aberto para você trabalhar.

## IR

```json
{"engine": 1, "name": "Thumb", "w": 1280, "h": 720, "layers": [
  {"id": "bg", "kind": "rect", "name": "BG", "opacity": 100, "box": [0, 0, 1280, 720], "radius": 0,
   "fill": [0.0549, 0.0667, 0.0863], "stroke": null, "stroke_w": 0.0},
  {"id": "card", "kind": "group", "name": "Card", "opacity": 100, "children": [ ... ]}
]}
```

`kind`: `rect`, `ellipse`, `line`, `path`, `text`, `image`, `group`. O IR é o contrato entre a cena e os players: um player
novo (SVG, Figma, o que for) só precisa ler este arquivo.
