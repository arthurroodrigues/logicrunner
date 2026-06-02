# Logic Runner

Jogo educativo em Python/Pygame inspirado em endless runners modernos. O jogador corre por uma faculdade cyberpunk em perspectiva third-person, troca de faixa, pula, desliza, desvia de obstaculos e escolhe portas com respostas de logica proposicional.

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

## Gerar assets procedurais

```bash
python generate_assets.py
```

Os sprites gerados ficam em `assets/generated/`.

## Controles

- `Seta esquerda` / `A`: mover para a esquerda
- `Seta direita` / `D`: mover para a direita
- `SPACE` / `W` / `Seta para cima`: pular
- `S` / `CTRL` / `Seta para baixo`: deslizar
- `ENTER` / `SPACE`: selecionar, iniciar ou continuar
- `P`: pausar
- `ESC`: voltar ou abrir pausa

## Gameplay

- Portas holograficas representam as respostas do desafio logico atual.
- Objetos nascem longe no eixo Z e crescem em perspectiva conforme se aproximam.
- O corredor usa segmentos infinitos com chao, paredes, teto, paineis e lanes em profundidade.
- O campus e gerado proceduralmente com chunks de corredor academico, biblioteca, laboratorio, cafeteria, area externa e setores raros.
- Obstaculos baixos exigem pulo.
- Obstaculos altos exigem slide.
- Bloqueios de faixa exigem desvio lateral.
- Powerups visuais incluem boost, ima, slow motion, escudo e multiplicador de score.
- Coletaveis incluem moedas, chips, paginas e dados holograficos.

O progresso e recordes sao salvos em `saves/save_data.json`.
