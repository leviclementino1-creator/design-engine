# Instalação (Windows)

## 1. O que a máquina precisa

| | para quê | observação |
|---|---|---|
| Python 3.10+ | tudo | `pip install -r requirements.txt` (Pillow e fontTools) |
| Photoshop | `--app ps` | qualquer versão com scripting; testado no Photoshop 28.2 (Beta) |
| Illustrator | `--app ai` | testado no Illustrator 31 (2027) |
| Windows PowerShell | `tools/run_jsx.ps1` | já vem no Windows |
| node | checar a sintaxe do `.jsx` gerado em `test_static.py` | opcional |

Você só precisa do app que for usar. O preview funciona sem nenhum dos dois.

## 2. Clonar e configurar

```
git clone https://github.com/<você>/design-engine.git
cd design-engine
pip install -r requirements.txt
copy config.example.json config.local.json
```

`config.local.json` nunca vai para o git. As chaves:

| chave | exemplo | |
|---|---|---|
| `brand` | `"demo"` | o pacote de marca ativo (`brands/<brand>/brand.py`) |
| `brands_dir` | `"D:/marcas"` | onde ficam os pacotes (padrão: `brands/` do repositório) |
| `ps_progid` | `"Photoshop.Application.BETA"` | o id COM do Photoshop; vazio = tenta a versão normal e depois a Beta |
| `ai_progid` | `"Illustrator.Application.31"` | o id COM do Illustrator; vazio = `Illustrator.Application` |
| `run_dir` | `"C:/temp/de_run"` | rascunho: `.jsx` gerado, log e PNG de conferência |
| `timeout` | `180` | segundos que um build pode levar |

Qualquer chave pode ser trocada por uma execução só: `set DE_BRAND=demo` (cmd) ou `DE_BRAND=demo python ...` (Git Bash).

## 3. Conferir o núcleo (sem app)

```
python test/test_static.py
python test/regress_ir.py compare test/regress_base_demo.json
```

O primeiro termina em `ALL OK`, o segundo em `REGRESSION: NONE (identical)`. Se o segundo acusar diferença só em `width` de
camadas de texto, a sua Arial é de outra versão que a da máquina que gravou a base: avise em vez de regravar a base.

## 4. Conferir dentro dos apps

Abra o Photoshop e/ou o Illustrator e rode:

```
python test/smoke.py
```

Ele constrói cada cena de teste num documento novo, fecha esse documento sem salvar e imprime um resumo com ordem e paridade.
As folhas lado a lado ficam em `test/out/smoke_<cena>_<app>.jpg`. App fechado aparece como `SKIPPED`.

## 5. A sua marca

Copie `brands/demo/` para `brands/<cliente>/`, troque o que o cliente precisa e ponha `"brand": "<cliente>"` no
`config.local.json`. Veja [brands/README.md](brands/README.md).

## 6. A skill do Claude Code (opcional)

```
xcopy /E /I skill\design-engine %USERPROFILE%\.claude\skills\design-engine
```

Depois diga ao Claude onde o repositório está (ou defina a variável de ambiente `DESIGN_ENGINE` com o caminho).

## Problemas comuns

| sintoma | causa e saída |
|---|---|
| `ABORT: Photoshop is not open` | o motor nunca abre o app: abra e rode de novo |
| `ABORT: ... did not answer over COM` | um diálogo modal está aberto no app, ou o id COM é outro: feche o diálogo ou ajuste `ps_progid` / `ai_progid` |
| `NO LOG after 180s` | o app está ocupado ou com diálogo aberto |
| `WARN font X not installed` | a fonte da marca não está instalada no sistema; o app usou a padrão dele |
| `PARITY ... DIFFERENT` | abra a folha (`--sheet`): a coluna da direita mostra em vermelho onde o app difere do preview |
