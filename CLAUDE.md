# design-engine: regras para o Claude Code

Leia o README.md e o docs/API.md antes de mudar qualquer coisa em `lib/`.

## Nunca

- Pôr nome de cliente, caminho de arquivo, cor ou fonte de cliente em `lib/`, `test/`, `examples/` ou na documentação. Material
  de cliente mora em `brands/<cliente>/` (fora do git). Valor novo que depende de marca = `config.b("NOME", padrao_neutro)` e
  uma linha em `brands/README.md`.
- Escrever caminho de máquina no código. Use `config.cfg("chave")`; configuração nova = uma chave em `SETTINGS`
  (`lib/config.py`) e em `config.example.json`.
- Commitar `config.local.json`, qualquer `brands/*` que não seja `demo`, `.psd`, `.ai`, renders, `out/`.
- Mandar script para o Photoshop ou o Illustrator por outro caminho que não `tools/run_jsx.ps1` (ele recusa com o app fechado).
- Abrir o app por script. O motor só fala com um app que o usuário abriu.
- Salvar, fechar ou alterar por script um documento que já estava aberto. Um build cria um documento NOVO e não o salva.
  `--close` só fecha o documento que aquele build criou.

## ExtendScript (`lib/runtime_*.jsx`)

- ES3: só `var`, sem arrow function, sem `let`/`const`, sem template string, sem `Array.prototype.map/forEach/indexOf/filter`,
  sem o objeto `JSON`, sem ternário encadeado sem parênteses. O `.jsx` gerado tem que ser ASCII.
  `python test/test_static.py` confere tudo isso.
- O cabeçalho de cada runtime lista as regras que ele mantém. Não afrouxe: cada uma existe por um erro que já aconteceu.
- Referência de camada do Photoshop tirada ANTES de criar outras camadas não é confiável depois: busque de novo pelo nome.
- Fonte ou imagem que falta = uma linha `WARN` no log, nunca um aborto.

## Python

- Mudança é aditiva: cena antiga tem que continuar gravando o mesmo IR. Antes de commitar:
  `python test/test_static.py` e `python test/regress_ir.py compare test/regress_base_demo.json`.
- Se o IR mudou de propósito, regrave a base no mesmo commit e escreva o porquê no CHANGELOG.
- Mudança num runtime precisa de `python test/smoke.py` com o app aberto; cole o resumo no PR.
- Os três players têm que concordar. Recurso novo entra no preview, no Photoshop e no Illustrator juntos, com uma cena
  `test/t_*.py` que o cobre, ou não entra.
- Nomes de camada e de grupo que vão para dentro do app são em inglês (outros designers abrem esses arquivos).

## Trabalho

- Uma linha no `CHANGELOG.md` por mudança do núcleo.
- Pedido de recurso ou bug de quem não mantém o repositório vai por issue.
