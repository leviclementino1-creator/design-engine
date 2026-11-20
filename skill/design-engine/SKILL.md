---
name: design-engine
description: Motor de design estático como dado para Photoshop e Illustrator. Uma cena em Python vira um IR (lista de camadas) que é tocado três vezes — preview em PNG (Pillow), documento em camadas no Photoshop aberto e documento vetorial no Illustrator aberto — e conferido por imagem (ORDER e PARITY). Use para thumbnail, capa, post, banner, card, cartela, peça de marca, ou qualquer arte que precise sair editável no Photoshop ou no Illustrator. Carregue ANTES de escrever qualquer cena, qualquer .jsx para Photoshop/Illustrator, ou de mexer em lib/ do design-engine.
---

# design-engine — design estático como dado

`ENGINE` abaixo = a pasta do repositório `design-engine` (a que tem `lib/engine.py`). Se a variável de ambiente
`DESIGN_ENGINE` existir, é ela. Se não souber onde está, pergunte ao usuário antes de procurar no disco.

A unidade de trabalho é a **cena**: um arquivo Python que monta um `Doc` e grava um `.ir.json`. O IR é o contrato. Nunca se
escreve `.jsx` à mão para montar uma arte: muda-se a cena e toca-se de novo.

```
briefing -> cena.py -> preview.png (aprovado) -> build no app -> ORDER OK + PARITY OK -> entrega
```

## Os portões (nesta ordem, inegociáveis)

| portão | comando | o que pega |
|---|---|---|
| a marca existe | `brands/<cliente>/brand.py` com `ACCENT`, `INK`, `PAPER`, `MUTED`, fontes e `FONT_FILES` | arte genérica, fonte que o app não tem |
| o texto cabe | `max_w=` em todo `d.text(...)` que mora dentro de um recipiente; `fit_size` / `wrap` para encaixar | estouro de borda descoberto no app |
| preview antes do app | `python ENGINE/lib/preview.py cena.ir.json cena.png`, **abrir e olhar a imagem** | conceito ruim descoberto cedo e barato |
| build conferido | `python ENGINE/lib/build.py cena.ir.json --app ps\|ai --sheet folha.jpg`, **abrir e olhar a folha** | camada fora de ordem, fonte trocada, forma diferente |
| núcleo intacto (só se mexeu em `lib/`) | `python ENGINE/test/test_static.py` e `python ENGINE/test/regress_ir.py compare ENGINE/test/regress_base_demo.json` | ES3 quebrado, cena antiga que mudou |

Erro em portão = parar e corrigir a **cena** (ou o núcleo), nunca o documento na mão.
Só diga que a arte está pronta depois de ter OLHADO o preview e a folha. `PARITY OK` sozinho não diz que a arte é boa, só que
o app fez o que o preview mostrou.

## Escrever uma cena

Leia `ENGINE/docs/API.md` antes da primeira cena da sessão. O essencial:

```python
import os, sys
sys.path.insert(0, r"<ENGINE>/lib")
from engine import Doc, ACCENT, INK, PAPER, MUTED, fit_size, wrap

d = Doc("Thumb EP12", 1280, 720, bg=INK)
with d.group("Card"):
    d.rect("Card bg", (88, 96, 760, 528), fill=PAPER, radius=36)
    s = fit_size(TITULO, 664, hi=120)
    d.text("Title", TITULO, (136, 300), size=s, fill=INK, leading=s * 1.08, max_w=664)
d.save("thumb_ep12.ir.json")
```

- Pixels, origem em cima à esquerda, y para baixo. `box = (x, y, largura, altura)`.
- As camadas vão de **baixo para cima**: a primeira escrita é o fundo.
- Texto é ancorado na **linha de base**, não no canto da caixa. Para pôr o topo das maiúsculas em `y0`, use
  `y = y0 + 0,72 × size` (Arial; confira no preview para outra fonte).
- Cores só as da marca. Uma cor de destaque (`ACCENT`), não cinco.
- Nomes de camada e de grupo em inglês e descritivos: outro designer vai abrir esse arquivo.
- A cena do cliente mora em `brands/<cliente>/`, nunca em `lib/` nem em `test/`.

## Trocar de cliente

`DE_BRAND=<cliente> python cena.py` (ou `"brand"` no `config.local.json`). As constantes `ACCENT`, `INK`... são lidas na
importação: uma cena não mistura duas marcas. Cliente novo = copiar `brands/demo/` e trocar valores. **Nunca editar `lib/`
para trocar de cliente.**

## Antes de mandar para o app

1. O app tem que estar **aberto pelo usuário**. O motor recusa com `ABORT` se não estiver, e você **não** abre o app para
   contornar: peça para abrir.
2. Nenhum diálogo modal aberto no app (senão `NO LOG` ou `did not answer over COM`).
3. As fontes da marca instaladas no sistema. `WARN font ...` no log = o app usou outra fonte: a arte **não** está certa,
   mesmo que o build tenha terminado.

O build cria um documento **novo** e o deixa aberto, sem salvar. Salvar, exportar a entrega e fechar são do usuário. Não use
`--close` em trabalho real: é para os testes.

## Ler o resultado do build

| linha | significa | o que fazer |
|---|---|---|
| `ORDER OK` | a árvore de camadas do app é a do IR | nada |
| `ORDER DIFFERENT - layer N ...` | uma camada caiu em outro lugar | bug do runtime: registrar e corrigir em `lib/`, com cena de teste |
| `PARITY 99.x% (OK)` | o app bate com o preview (o resto é anti-aliasing) | olhar a folha mesmo assim |
| `PARITY ... DIFFERENT` | menos de 97% igual | abrir a folha: a coluna da direita mostra em vermelho onde |
| `WARN font X not installed` | fonte trocada | instalar a fonte ou corrigir o nome PostScript na marca |
| `WARN image missing` | a camada de imagem foi pulada | corrigir o caminho na cena |
| `ABORT ...` | nada foi enviado | ler a mensagem; quase sempre é o app fechado |

## O que o motor NÃO faz (diga isso ao usuário quando for o caso)

- Gradiente, sombra, efeito de camada, máscara, texto de parágrafo, curva Bézier, várias pranchetas.
- Editar um documento que já existe: ele só constrói documento novo.
- macOS.
- Decidir se a ideia é boa. Ele estrutura a decisão e garante que o que foi aprovado é o que foi entregue.

Se a peça precisa de algo dessa lista: construa a base com o motor e diga claramente o que fica para finalizar à mão no app
(ou, se o recurso vai se repetir, proponha adicioná-lo ao núcleo: nos três players, com cena de teste).

## Edição pontual num documento já aberto

Não é o motor: é script avulso. Se existirem MCPs de Photoshop ou Illustrator na sessão, eles servem para isso (ler o
estado do documento, trocar um texto, exportar). Mesmas regras: nunca salvar por cima nem fechar documento do usuário sem
ele pedir, e ExtendScript é ES3 (sem `let`/`const`, arrow function, template string, `JSON`, `Array.map/forEach`).

## Mexer no núcleo (`lib/`)

Leia `ENGINE/CLAUDE.md`. Resumo: mudança aditiva, os três players juntos, cena `test/t_*.py` que cobre, `test_static.py` +
`regress_ir.py compare` antes de commitar, `test/smoke.py` com os apps abertos se tocou num runtime, uma linha no
`CHANGELOG.md`.
