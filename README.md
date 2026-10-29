# Roblox на Arch Linux — моя сборка (Mocktail)

Набор скриптов, который повторяет мою настройку Roblox на Arch Linux:
Mocktail из Flathub, звук через PipeWire, отключённый libdecor, настройки
производительности, курсор Roblox Legacy (чёрная стрелка) и запуск одной
командой `roblox`.

Проверено на Arch x86_64, KDE Plasma 6 (Wayland); также работает под niri.

> Это **не сам Roblox**. Бинарники Roblox и Mocktail здесь не лежат — они
> ставятся из Flathub. Нужен свой аккаунт Roblox. Проект не связан с Roblox
> Corporation. Mocktail — сторонний экспериментальный рантайм.

## Что получится

- `roblox` в терминале запускает игру с нужными переменными окружения
- звук идёт через PipeWire, без `pipewire-pulse`
- окно без белой полосы-заголовка (отключён libdecor)
- многоядерный рендер Roblox (`multithreaded_rendering`, `throughput`)
- курсор из старых Roblox 2006–2013 (чёрная стрелка с длинным хвостом)
- опционально: включение Intel Turbo Boost для стабильных FPS

## Требования

- Arch Linux x86_64
- Wayland-сессия (KDE Plasma 6 или niri)
- Flatpak + Flathub
- PipeWire (обычно уже стоит)
- Vulkan-драйвер для вашей видеокарты
- `python-pillow` для сборки курсоров

```bash
sudo pacman -S flatpak python-pillow
```

## Установка

```bash
git clone https://github.com/bebrick16-beep/roblox-linux-setup.git
cd roblox-linux-setup
chmod +x install.sh scripts/*.sh scripts/*.py
./install.sh
```

Скрипт:

1. ставит `space.bigrat.mocktail` из Flathub;
2. открывает песочнице доступ к сокету PipeWire;
3. кладёт запускалку в `~/.local/bin/roblox`;
4. применяет настройки Mocktail (многоядерный рендер, Vulkan);
5. собирает и ставит тему курсора `RobloxLegacy`;
6. в KDE сразу применяет курсор.

Если `~/.local/bin` нет в `PATH`, добавьте в `~/.bashrc` / `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Первый запуск

```bash
roblox
```

Первый старт скачивает payload Roblox. Если при входе чёрный экран — это
известная ошибка WebKit в песочнице; запускалка уже содержит обход
(`WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1`). Выберите **Quick login**.

После того как payload скачался, закройте игру и один раз перезапустите
установку, чтобы собрать курсоры из файлов игры:

```bash
./install.sh
```

## Курсор

Тема `RobloxLegacy` — чёрная стрелка из пака «Roblox Legacy Cursors
2006–2013», плюс рука и текстовый курсор из самой игры. Картинки не хранятся
в репозитории: скрипт скачивает публичный превью-пак и извлекает текстуры из
вашего локального payload.

KDE:

```bash
plasma-apply-cursortheme RobloxLegacy
```

или System Settings → Appearance → Cursors → **RobloxLegacy**, размер 24.
Если курсор не сменился сразу — перезайдите в сессию.

Внутри игры курсор применяется после полного перезапуска `roblox`
(запускалка передаёт `XCURSOR_THEME`).

## Звук

Звук работает через PipeWire-сокет, доступ к которому выдаёт `install.sh`.
Если тихо:

```bash
flatpak override --user --filesystem=xdg-run/pipewire-0 space.bigrat.mocktail
systemctl --user status pipewire wireplumber
```

## Производительность

Проверьте, не выключен ли Turbo Boost:

```bash
cat /sys/devices/system/cpu/intel_pstate/no_turbo
```

`1` = выключен. Включить (временно, до перезагрузки):

```bash
sudo ./scripts/enable-turbo.sh
```

Это заметно повышает FPS, но и температуру. Если ноутбук горячий — не
включайте или ограничьте частоту.

## Белая полоса сверху

За неё отвечает libdecor (клиентские заголовки SDL). Запускалка выставляет
`SDL_VIDEO_WAYLAND_ALLOW_LIBDECOR=0`, поэтому полосы нет.

## Скриншоты (KDE)

По умолчанию снимает Spectacle. Чтобы весь экран снимался по F10:

System Settings → Shortcuts → Spectacle → **Capture Entire Screen** → задать
`F10`.

## niri (опционально)

Если используете niri, добавьте в `~/.config/niri/config.kdl`:

```kdl
cursor {
    xcursor-theme "RobloxLegacy"
    xcursor-size 24
}
```

и бинд:

```kdl
F10 allow-inhibiting=false { screenshot-screen; }
```

Затем `niri validate` и перезагрузите конфиг (niri перечитывает его сам).

## Если что-то не так

- **Чёрный экран при входе** — обход уже в запускалке; используйте Quick login.
- **Нет звука** — проверьте override и что PipeWire запущен.
- **Курсор старый** — перезайдите в сессию; в игре — перезапустите `roblox`.
- **Лаги** — включите Turbo Boost (см. выше), проверьте Vulkan-драйвер.
- **Ошибки `DnsResolve` в логах** — проблема DNS/сети, не установки.

## Лицензия

Скрипты — MIT. Roblox, Mocktail и сторонние курсоры принадлежат их авторам.
