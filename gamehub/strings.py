"""i18n PT-BR / EN do GameHub."""

STRINGS: dict[str, tuple[str, str]] = {
    "app_title": ("GameHub", "GameHub"),
    "all": ("Todos os jogos", "All games"),
    "search": ("Buscar jogo…", "Search game…"),
    "settings": ("Configurações", "Settings"),
    "rescan": ("Reescanear biblioteca", "Rescan library"),
    "games_n": ("{n} jogos", "{n} games"),
    "scanning": ("Escaneando…", "Scanning…"),
    "play": ("Jogar", "Play"),
    "stop": ("Parar", "Stop"),
    "running": ("Rodando: {name}", "Running: {name}"),
    "favorite": ("Favoritar", "Favorite"),
    "unfavorite": ("Desfavoritar", "Unfavorite"),
    "verify": ("Verificar integridade", "Verify integrity"),
    "open_folder": ("Abrir pasta do jogo", "Open game folder"),
    "delete_rom": ("Apagar jogo", "Delete game"),
    "delete_confirm": ("Mover este jogo pra lixeira do sistema?",
                       "Move this game to the system trash?"),
    "delete_confirm2": ("Confirma? A pasta vai pra lixeira (dá pra restaurar).",
                        "Sure? The folder goes to trash (restorable)."),
    "verify_title": ("Jogo", "Game"),
    "verify_ok": ("Nenhum arquivo zerado", "No zeroed files"),
    "verify_damaged": ("ATENÇÃO: arquivos zerados — conteúdo danificado",
                       "WARNING: zeroed files — damaged content"),
    "no_emulator": ("Sem emulador para {s}.\nAbra Configurações e aponte um "
                    "AppImage em cores/.", "No emulator for {s}.\nOpen Settings "
                    "and point to an AppImage in cores/."),
    "no_emulator_dl": ("Dica: em Configurações → Emuladores, clique em "
                       "“Baixar AppImage” ({name}).",
                       "Tip: in Settings → Emulators, click "
                       "“Download AppImage” ({name})."),
    "no_core": ("Core \"{core}\" não encontrado na pasta dos cores.\n"
                "Configurações → Emuladores → pasta dos cores.",
                "Core \"{core}\" not found in the cores folder.\n"
                "Settings → Emulators → cores folder."),
    "launch_failed": ("Falha ao iniciar o jogo.", "Failed to start the game."),
    "last_played": ("último: {when}", "last: {when}"),
    # ---- settings ----
    "cfg_title": ("Configurações", "Settings"),
    "cfg_general": ("Geral", "General"),
    "cfg_emulators": ("Emuladores", "Emulators"),
    "cfg_romdirs": ("Pastas de ROM", "ROM folders"),
    "cfg_pc": ("Jogos PC", "PC games"),
    "cfg_language": ("Idioma", "Language"),
    "cfg_gamemode": ("Usar GameMode (gamemoderun) ao jogar",
                     "Use GameMode (gamemoderun) when playing"),
    "cfg_icon_size": ("Tamanho dos ícones", "Icon size"),
    "cfg_system": ("Sistema", "System"),
    "cfg_binary": ("Executável", "Executable"),
    "cfg_args": ("Argumentos ({game} = jogo)", "Arguments ({game} = game)"),
    "cfg_browse": ("Procurar…", "Browse…"),
    "cfg_detect": ("Detectar", "Detect"),
    "cfg_dl_appimage": ("Baixar AppImage", "Download AppImage"),
    "cfg_appi_hint": ("Binário oficial — baixa pra pasta cores/ do GameHub; "
                      "nada é instalado no sistema.",
                      "Official binary — downloads into GameHub's cores/ "
                      "folder; nothing is installed system-wide."),
    "cfg_appi_none": ("“{name}” não tem binário AppImage. {info}",
                      "“{name}” has no AppImage build. {info}"),
    "cfg_dl_start": ("Baixando {name}…", "Downloading {name}…"),
    "cfg_dl_done": ("✔ {file} baixado e configurado.", "✔ {file} downloaded and configured."),
    "cfg_dl_fail": ("Falha no download: {err}", "Download failed: {err}"),
    "cfg_dl_noresource": ("Sem AppImage nesta fonte.", "No AppImage available from this source."),
    "cfg_sa_note": ("💡 Dica: o emulador standalone é sempre melhor que o "
                    "RetroArch — mais fiel, mais rápido e com menos input lag. "
                    "Mas a escolha é sua: se preferir, use o core.",
                    "💡 Tip: the standalone emulator is always better than "
                    "RetroArch — more accurate, faster and with less input lag. "
                    "But the choice is yours: pick the core if you prefer."),
    "cfg_add": ("Adicionar", "Add"),
    "cfg_remove": ("Remover", "Remove"),
    "cfg_add_folder": ("Adicionar pasta de ROM", "Add ROM folder"),
    "cfg_add_exe": ("Adicionar executável", "Add executable"),
    "cfg_pc_name": ("Nome", "Name"),
    "cfg_cores_hint": ("Coloque os AppImages dos emuladores em cores/ — o "
                       "GameHub detecta por nome. Também vale binário solto.",
                       "Drop emulator AppImages into cores/ — GameHub detects "
                       "them by name. Loose binaries work too."),
    "cfg_ra_cores": ("Pasta dos cores do RetroArch", "RetroArch cores folder"),
    "cfg_ra_cores_hint": ("Pasta que contém apenas os cores (*.so). Vale pra "
                          "todos os sistemas retro.",
                          "Folder containing only the cores (*.so). Applies to "
                          "all retro systems."),
    "cfg_ra_embed": ("Baixar RetroArch (embutido)", "Download RetroArch (embedded)"),
    "cfg_saved": ("Configurações salvas", "Settings saved"),
    "cfg_not_exec": (" Marcado como executável (chmod +x).",
                     " Marked executable (chmod +x)."),
    # --- regras do hub: standalone ↔ core ---
    "cfg_standalone": ("Emulador standalone (preferido)",
                       "Standalone emulator (preferred)"),
    "cfg_use_core": ("Usar core do RetroArch", "Use RetroArch core"),
    "cfg_core_pick": ("Core do RetroArch", "RetroArch core"),
    "cfg_no_compat_core": ("Nenhum core compatível com este sistema na pasta de "
                           "cores.", "No compatible core for this system in the "
                           "cores folder."),
    "cfg_update_core": ("Atualizar core", "Update core"),
    "cfg_updating": ("Atualizando core…", "Updating core…"),
    "cfg_fullscreen": ("Abrir em tela cheia", "Open in fullscreen"),
    "cfg_fullscreen_tip": ("Tela cheia direto no jogo — nunca mostra o menu do "
                           "RetroArch.", "Fullscreen straight into the game — "
                           "never shows the RetroArch menu."),
    "cfg_fs_unsupported": ("Este emulador não aceita tela cheia por argumento — "
                           "configure dentro dele.", "This emulator doesn't accept "
                           "fullscreen via argument — set it inside the emulator."),
    # --- aba Geral: opções do RetroArch ---
    "cfg_shader": ("Filtro visual", "Video filter"),
    "cfg_resolution": ("Resolução (tela cheia)", "Resolution (fullscreen)"),
    "cfg_aspect": ("Proporção de tela", "Aspect ratio"),
    "cfg_detect_controls": ("Detectar controles", "Detect controllers"),
    "cfg_no_controls": ("Nenhum controle detectado", "No controller detected"),
    "cfg_core_auto": ("Atualizar cores automaticamente", "Auto-update cores"),
    # --- sidebar colapsável ---
    "sidebar_toggle": ("Recolher/expandir o menu lateral", "Collapse/expand the sidebar"),
    # --- gamepad ---
    "gamepad_on": ("Controle detectado: {name} — navegue na grade com o D-pad",
                   "Controller detected: {name} — navigate the grid with the D-pad"),
    # --- capas / ScreenScraper ---
    "cfg_covers": ("Capas (imagens dos jogos)", "Covers (game art)"),
    "cfg_ss_hint": ("Capas vêm do Libretro Thumbnails (grátis, sem conta). "
                    "Preencha o ScreenScraper pra cobrir mais jogos (busca por "
                    "nome) — credenciais grátis em screenscraper.fr.",
                    "Covers come from Libretro Thumbnails (free, no account). "
                    "Fill in ScreenScraper to cover more games (name search) — "
                    "free credentials at screenscraper.fr."),
    "cfg_ss_user": ("Usuário", "User"),
    "cfg_ss_pass": ("Senha", "Password"),
    "cfg_ss_on": ("ScreenScraper: ativo (fallback de capas)",
                  "ScreenScraper: active (cover fallback)"),
    "cfg_ss_off": ("ScreenScraper: desligado (sem credencial)",
                   "ScreenScraper: off (no credentials)"),
    # --- capas ---
    "dl_covers": ("Baixar capas (Libretro Thumbnails)", "Download covers (Libretro Thumbnails)"),
    "dl_covers_start": ("Baixando capas… ({n} jogos) — clique de novo pra parar",
                        "Downloading covers… ({n} games) — click again to stop"),
    "dl_covers_progress": ("Capa {i}/{total}: {title}", "Cover {i}/{total}: {title}"),
    "dl_covers_done": ("Capas: {ok} baixadas de {total}", "Covers: {ok} downloaded of {total}"),
    # --- cheats ---
    "cheats_menu": ("Cheats", "Cheats"),
    "cheats_title": ("Cheats", "Cheats"),
    "cheats_loading": ("Procurando cheats deste jogo…", "Looking for this game's cheats…"),
    "cheats_none": ("Nenhum cheat disponível para este jogo.",
                    "No cheats available for this game."),
    "cheats_empty": ("O arquivo de cheat deste jogo não tem itens.",
                     "This game's cheat file has no items."),
    "cheats_net": ("Falha de rede ao baixar os cheats — tente de novo.",
                   "Network failed while downloading cheats — try again."),
    "cheats_found": ("{n} cheats — marque os desejados e salve.",
                     "{n} cheats — check the ones you want and save."),
    "cheats_filter": ("Filtrar cheat…", "Filter cheat…"),
    "cheats_all": ("Marcar todos", "Select all"),
    "cheats_none_sel": ("Limpar seleção", "Clear selection"),
    "cheats_retry": ("Tentar de novo", "Try again"),
    "cheats_saved": ("Cheats salvos! Entram em ação na próxima vez que o "
                     "jogo abrir.", "Cheats saved! They take effect next time "
                     "the game opens."),
    "save": ("Salvar", "Save"),
    "cancel": ("Cancelar", "Cancel"),
}


def tr(cfg, key: str, **kwargs) -> str:
    lang = "pt" if cfg["language"] != "en" else "en"
    text = STRINGS.get(key, (key, key))[0 if lang == "pt" else 1]
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text
