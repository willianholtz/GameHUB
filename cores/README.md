# cores/ — Emuladores do GameHub

Jogue aqui os **AppImages (ou binários standalone)** dos emuladores.
O GameHub detecta pelo nome do arquivo — não precisa renomear nada,
mas pode se quiser (ex.: `PCSX2.AppImage`).

**RetroArch**: em vez de instalar, use o botão **"Baixar RetroArch
(embutido)"** em ⚙ Configurações → Emuladores — ele baixa o binário
oficial portátil pra `vendor/retroarch/` dentro do projeto. Cores continuam
apontados pela Configurações → "Pasta dos cores".

Detectáveis por regex no nome:

| Sistema | Emulador | Onde baixar |
|---|---|---|
| PS4 | shadPS4 | github.com/shadps4-emu/shadPS4 (releases) |
| PS3 | RPCS3 | rpcs3.net (releases) |
| PS2 | PCSX2 | pcsx2.net (releases) |
| PS1 | DuckStation | duckstation.standalone.info |
| PSP | PPSSPP | ppsspp.org (releases) |
| Switch | Eden | github.com/eden-emu/eden (releases) |
| 3DS | Azahar | github.com/azahar-emu/azahar (releases) |
| Wii/GC | Dolphin | dolphin-emu.org (releases) |
| Xbox | xemu | xemu.app (releases) |
| Dreamcast | redream | redream.io |
| Retro | RetroArch | retroarch.com (cores ficam em ~/.config/retroarch/cores) |

Obs.:

- AppImage precisa de permissão de execução — o GameHub faz `chmod +x`
  sozinho quando você escolhe o arquivo pela Configurações.
- Também vale binário solto extraído de tarball (ex.: `PPSSPPSDL`).
- Sem AppImage de um emulador? Ele usa o binário instalado no sistema
  (PATH) automaticamente como fallback.
