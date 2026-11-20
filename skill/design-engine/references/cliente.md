# Descoberta do cliente

Antes da primeira cena de um cliente novo. Sai daqui com dois arquivos em `brands/<cliente>/`:

- `brand.py`: os valores (cores, fontes), que o motor lê.
- `ESTILO.md`: o que os valores não dizem (composição, tom, o que nunca fazer), que VOCÊ lê no começo de toda sessão.

Sem os dois, a arte sai genérica: certa no pixel e errada para o cliente.

## 1. Pedir o material (uma mensagem só)

Peça tudo de uma vez, e diga que pouco material é melhor que nenhum:

1. **Peças que já foram ao ar**: 5 a 15 artes finais do cliente (thumbnails, posts, capas), em imagem. De preferência as que
   ele mais gosta e as que performaram melhor, dizendo quais são quais.
2. **Arquivos de projeto**: `.psd` / `.ai` de uma ou duas dessas peças, se existirem. Mostram a estrutura de camadas, as
   fontes reais e as medidas.
3. **Material de marca**: manual, style guide, logo, paleta, arquivos de fonte.
4. **Referências de fora**: peças de outros canais ou marcas que ele admira, e peças que ele NÃO quer parecer.
5. **Onde a peça vai**: plataforma, tamanho em pixels, e se existe versão pequena (celular, miniatura).

Se o usuário não tiver algum item, siga com o que tem e anote a lacuna no `ESTILO.md`. Não invente o que falta.

## 2. As perguntas (só as que o material não respondeu)

Olhe o material ANTES de perguntar. Não pergunte o que dá para ver. Do que sobrar, pergunte de uma vez:

- **Quem vê** essa peça e o que precisa entender em um segundo?
- **Três palavras** para o tom (ex.: calmo, técnico, quente) e três que ele NÃO é.
- **O que nunca pode aparecer**: cor, tipo de imagem, palavra, efeito, clichê do nicho.
- **Texto**: caixa alta ou não, quantas palavras no máximo, quem escreve o título.
- **Rosto e imagem**: usa foto de pessoa? Recortada? De onde vêm as imagens, e quem tem o direito de uso?
- **O que varia e o que é fixo** de uma peça para a outra (o que é série, o que é identidade).
- **Quem aprova** e o que já foi reprovado antes, e por quê.

Recuse resposta vaga. "Moderno e clean" não é resposta: peça uma peça que mostre o que ele quer dizer.

## 3. Analisar o material

Abra cada imagem e olhe de verdade. Para os arquivos de projeto, leia a estrutura pelo app aberto (MCP ou script de leitura,
nunca alterando nem salvando o arquivo do cliente). Meça, não estime:

| o que | como medir | vira |
|---|---|---|
| paleta | as cores que ocupam área de verdade em cada peça (amostrar pixels, agrupar); separar fundo, texto, destaque | `ACCENT`, `INK`, `PAPER`, `MUTED` |
| quantas cores de destaque | contar por peça | regra no `ESTILO.md` (uma é o normal) |
| fontes | nome PostScript nas camadas de texto do `.psd`/`.ai`; sem arquivo, perguntar. Não chute fonte pela aparência | `FONT_DISPLAY`, `FONT_BODY`, `FONT_FILES` |
| escala do texto | altura do título ÷ altura da peça; nº de palavras; nº de linhas | faixa de tamanho no `ESTILO.md` |
| margens e grade | distância do conteúdo até as bordas, em % da largura | margem segura no `ESTILO.md` |
| formas | canto reto ou arredondado (raio ÷ lado menor), contorno ou preenchimento, espessura | regra de forma |
| composição | onde fica o título, onde fica a imagem, para onde o olho vai primeiro | os 2 ou 3 layouts que se repetem |
| o que repete | o que aparece em TODAS as peças boas | identidade (fixo) |
| o que muda | o que só aparece em algumas | variação permitida |

Compare as peças que ele gosta com as que não gosta: a diferença entre os dois grupos é a regra mais valiosa que existe, e
quase nunca está no manual.

Diga o que NÃO deu para saber (fonte sem arquivo, só duas peças de amostra, peças que se contradizem). Uma regra tirada de
três peças é uma hipótese: escreva como hipótese.

## 4. Escrever `brand.py` e `ESTILO.md`

`brand.py`: copie `brands/demo/brand.py`, troque só o que mediu. Confira que cada arquivo de `FONT_FILES` existe e que a
fonte está instalada (senão o app troca a fonte e a medida mente).

`ESTILO.md`: use `brands/demo/ESTILO.md` como gabarito. Regras curtas e verificáveis ("título em caixa alta, no máximo 5
palavras, 2 linhas"), não adjetivos ("tipografia forte"). Cada regra com a peça de onde saiu.

## 5. Devolver para o usuário antes de desenhar

Mostre, em poucas linhas: a paleta com os hex, as fontes, as 5 a 8 regras que você tirou, e as dúvidas. Peça correção. Só
depois disso a primeira cena. O que o usuário corrigir entra no `ESTILO.md` na hora, com a data.

## 6. Manter vivo

- Peça reprovada ou corrigida à mão pelo designer = uma regra nova no `ESTILO.md` (o que mudou e por quê). É assim que a
  próxima sessão não repete o erro.
- No começo de toda sessão de um cliente que já existe: ler `ESTILO.md` inteiro antes de escrever cena.
- Material do cliente (peças, `.psd`, fontes, manual) fica em `brands/<cliente>/`, que está fora do git. Nunca vai para o
  repositório nem para nenhum serviço externo sem o usuário pedir.
