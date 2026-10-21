# 🎮 GameHub

**Um launcher unificado pra toda a sua biblioteca: emuladores + jogos de PC,
numa grade só, com capas bonitas — e sem instalar nada no sistema.**

Feito em **PySide6**, tema escuro, i18n (PT/EN) e configuração **100%
portátil**: tudo mora dentro da pasta do projeto.

## Por que o GameHub existe

Eu cansei de três coisas:

1. **Emulador espalhado pela máquina** — cada um com config em `~/.config`,
   saves em pasta diferente, atualização por conta própria. Queria o
   contrário: copiei a pasta `GameHUB` pra um PC novo, pluguei os HDs de
   ROM e está tudo lá — **portátil de verdade**.
2. **Instalar coisa no sistema só pra jogar** — AppImage é o caminho: baixa,
   roda, some. Por isso o GameHub baixa os emuladores pra dentro dele mesmo
   (e a config deles também fica dentro — ver `emu-data/` abaixo).
3. **Menu no meio do jogo** — abrir o jogo e **ele já abrir**, em tela cheia,
   sem passar pelo menu do RetroArch nem por assistente de primeira execução.

O resultado é esse aqui: um "Netflix dos jogos retrô" que respeita o
computador em que roda — e que tem cara de launcher de respeito (ícones de
console reais, capas de verdade, tudo coeso).

## Como funciona

| Pasta | O que mora nela |
|---|---|
| `cores/` | **AppImages/binários dos emuladores.** Detecção automática por nome — ou clique em **Baixar AppImage** nas Configurações (veja abaixo). |
| `config/` | `front.json` — pastas de ROM, emulador por sistema, favoritos, últimos jogados. Apaga a pasta, some tudo. |
| `emu-data/` | **Config/saves/cache dos AppImages** que rodam de `cores/`. Cada emulador recebe um `HOME` próprio dentro do projeto: **nada é escrito no `~/.config` do sistema**. |
| `vendor/retroarch/` | RetroArch embutido (portátil, com kiosk mode e cheats). |
| `assets/systems/` | Ícones reais dos consoles da barra lateral (créditos em `CREDITS.txt`). |
| `cache/` | Capas baixadas. |

### Baixar emuladores pela própria interface

⚙ **Configurações → Emuladores** → escolha o sistema → **Baixar AppImage**:

- O GameHub consulta a **release oficial** (GitHub ou Gitea do projeto),
  baixa o build **x86_64 certo** pra `cores/`, marca como executável e
  configura o sistema sozinho.
- **Disponível hoje:** PCSX2 (PS2), DuckStation (PS1), PPSSPP (PSP),
  Azahar (3DS), Eden (Switch), Cemu (Wii U), xemu (Xbox), Vita3K, Flycast.
- **Sem AppImage oficial:** a própria interface avisa e mostra onde baixar
  (RPCS3, shadPS4, Dolphin e redream publicam só tar.gz/.zip).

### Standalone × core do RetroArch

Cada sistema roda no **emulador standalone** (preferencial) ou num **core do
RetroArch** — quando o sistema tem **as duas opções**, uma faixa na
Configurações lembra: *standalone é sempre melhor (mais fiel, mais rápido,
menos input lag), mas a escolha é sua*. Sistemas sem core compatível ficam
com a opção de core desabilitada — sem erro, sem confusão.

## Como usar

```bash
pip install -r requirements.txt   # só PySide6
./run.py
```

1. ⚙ **Configurações → Emuladores** → **Baixar AppImage** dos sistemas que
   quiser (ou jogue seus próprios AppImages em `cores/`)
2. ⚙ **Configurações → Pastas de ROM** → adicione suas pastas (várias por
   sistema, ex.: PS2 em 2 HDs)
3. 📥 clique no botão de capas pra preencher a biblioteca
4. **Duplo clique pra jogar** (usa GameMode se `gamemoderun` existir;
   o jogo abre em tela cheia, sem menu)
5. (opcional) tem `gamelist.xml` na pasta da ROM (padrão ES-DE)? Ele lê
   sozinho — gênero, nota e descrição aparecem no **Detalhes** de cada jogo

## Recursos

- **Capas automáticas** — botão 📥 baixa do **Libretro Thumbnails** (oficial,
  grátis) pelo nome da ROM; cache no projeto. Fallback **ScreenScraper**
  (credencial grátis em Configurações → Geral) cobre o que a base oficial não
  acha. Sem capa, placeholder com gradiente.
- **Metadados de verdade (gamelist.xml)** — joga um `gamelist.xml` (padrão
  EmulationStation/ES-DE) na pasta da ROM e o GameHub lê nome, gênero, nota
  e descrição — o `<name>` vira o título da grade. XML quebrado não derruba
  a biblioteca.
- **Tela de detalhes** — botão direito → **Detalhes**: ícone grande, título,
  sistema, gênero, nota (X/10), descrição e caminho, com **Jogar** ali
  mesmo.
- **Cheats sem menu** — botão direito no jogo → **Cheats**: lista os trapaças
  do `.cht` oficial (baixa automaticamente), marque e salve. Ao abrir o jogo,
  o RetroArch carrega e aplica sozinho — o menu nunca aparece. Só em sistemas
  em modo core (onde há base de cheats).
- **Jogo abre direto** — kiosk mode no RetroArch embutido: bloqueia o menu,
  deixa F11 (tela cheia), P (pausa) e ESC 2× (sair). Fullscreen/janela por
  emulador.
- **Filtros, resolução e proporção** (aba Geral) — CRT, LCD, suave, nítido;
  até 4K; 4:3 / 16:9 / 1:1.
- **RetroArch embutido** — ⚙ → Emuladores → "Baixar RetroArch (embutido)"
  baixa o build oficial portátil pra `vendor/` (config própria, kiosk,
  cheats — tudo dentro do projeto).
- **Cores atualizáveis** — por demanda (botão) ou automático (a cada 7
  dias), direto do buildbot oficial do Libretro.
- **Ícones reais dos consoles** — barra lateral e Configurações →
  Ilustrações vetoriais de verdade (KyleBing CC-BY 4.0, Controllercons
  SIL OFL 1.1; 3DS e 3DO autorais) — ver `assets/systems/CREDITS.txt`.
- **Controles** — detecta gamepads; navega a grade pelo D-pad/analógico:
  A joga, B volta, Start abre config. Plugou, já funciona.
- **Grade com capas reais** — icon0.png do PS4, ICON0 do PS3 (das pastas
  **ou de dentro do `.iso`**, case-insensitive — igual o RPCS3 puxa), capas
  baixadas ou `jogo.png` ao lado da ROM; badge do emulador em cada jogo.
- Busca, filtro por sistema na barra lateral, favoritos (★), último jogado.
- Menu por botão direito: **detalhes**, jogar/parar, favoritar,
  **verificar integridade** (detecta arquivos zerados), abrir pasta,
  **apagar** (lixeira com confirmação dupla).
- **Tray icon enquanto joga** — o GameHub some pra bandeja com o título do
  jogo no tooltip; botão direito na bandeja: **Mostrar / Parar / Sair**.
- **Configuração levo** — ⚙ → Geral → **Exportar/Importar configuração**:
  um `.json` com tudo (pastas de ROM, emuladores, favoritos). No PC novo,
  importou e era. Importar pede confirmação (substitui a atual).
- **F11** alterna tela cheia da janela; **Ctrl+scroll** redimensiona os
  ícones; **sidebar colapsável** (só ícones dos consoles, com dica).
- Suporte a: PS4 (pastas CUSA), PS3 (RPCS3), PS2, PS1, PSP, Switch, 3DS,
  Wii, GC, N64, DS, GB/GBC/GBA, SNES, NES, Famicom, FDS, Mega Drive, SMS,
  Game Gear, Mega CD, Dreamcast, Saturn, PC Engine/CD, SuperGrafx, Neo Geo,
  Atari 2600/5200, Lynx, WonderSwan, Virtual Boy, Vectrex, MSX, Neo Geo
  Pocket, Arcade (FBNeo), Xbox e PC nativo.

## Estrutura

```
GameHUB/
├── run.py              # entry point
├── gamehub/
│   ├── app.py          # janela principal (modelo + delegate + menus)
│   ├── appstore.py     # loja de AppImages oficiais (GitHub/Gitea)
│   ├── catalog.py      # sistemas, emuladores e catálogo de cores
│   ├── cheats.py       # cheats do RetroArch (.cht) sem menu
│   ├── config.py       # config portátil (config/front.json)
│   ├── controls.py     # detecção de gamepads
│   ├── covers.py       # capas automáticas (Libretro Thumbnails)
│   ├── details.py      # tela de detalhes do jogo (ícone grande + meta)
│   ├── gamepad.py      # navegação da grade pelo controle
│   ├── gamelist.py     # metadados por jogo (gamelist.xml, padrão ES-DE)
│   ├── icons.py        # badges de emulador + ícones reais dos consoles
│   ├── iso9660.py      # leitor de ISO9660 (ícone/título de PS3 .iso)
│   ├── ra_vendor.py    # RetroArch portátil + cores + filtros + cheats
│   ├── screenscraper.py # fallback de capas (ScreenScraper)
│   ├── scanner.py      # varredura multi-pasta por sistema
│   ├── runners.py      # resolução, sandbox emu-data e lançamento
│   ├── settings.py     # diálogo de configurações
│   ├── sfo.py          # leitor de PARAM.SFO
│   ├── strings.py      # i18n PT-BR / EN
│   └── thumbindex.py   # índice de capas
├── assets/systems/     # ícones dos consoles (CREDITS.txt)
├── cores/              # AppImages dos emuladores (ou Baixar AppImage)
├── emu-data/           # config/saves dos AppImages (gitignorado)
├── vendor/             # RetroArch portátil (gerado, gitignorado)
├── cache/              # capas baixadas (gerado, gitignorado)
└── config/             # front.json (criado na 1ª execução)
```

## Roadmap

- [x] PS3: ícones/títulos como o RPCS3 puxa — pastas PKG e dumps
  `PS3_GAME/` com busca case-insensitive (Linux não perdoa `EBOOT.BIN`),
  e `.iso` (PS3ISO) com `ICON0.PNG`/`PARAM.SFO` lidos de dentro da
  imagem (camada ISO9660; dump bruto só-UDF cai na capa automática)
- [x] Metadados por jogo (nota, gênero, descrição) via `gamelist.xml`
  (padrão EmulationStation/ES-DE) — o `<name>` vira o título
- [x] Tela de detalhes do jogo (botão direito → Detalhes)
- [x] Tray icon enquanto joga (Mostrar / Parar / Sair)
- [x] Export/import da config (Configurações → Geral)

## Licença

MIT. Ícones de terceiros sob suas próprias licenças
(`assets/systems/CREDITS.txt`): CC BY 4.0 (KyleBing) e
SIL OFL 1.1 (Controllercons).
