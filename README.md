# Megafon Desktop

Native Windows desktop manager for **consumer** MegaFon accounts.

The project replaces a legacy Excel/VBA workflow with a maintainable application:

- multiple accounts in one local database;
- HTTP-only reverse integration with the consumer web cabinet;
- persistent per-account HTTP authorization protected by Windows DPAPI;
- interactive CAPTCHA inside the desktop application;
- explicit user-triggered refresh of selected accounts;
- balances, latest activity, personal offers, available options and number blocking;
- no browser extension, no browser runtime dependency, no B2B scope, and no official MegaFon API dependency.

> The consumer MegaFon endpoints used by this project are internal, undocumented interfaces and
> may change without notice. Network behavior is therefore isolated behind transport interfaces.

## Current status

`v0.3.0` is the current Windows build.

### v0.3.0

- restored **Обновить выбранные** and removed **Обновить всё**;
- removed the per-row actions column; **Удалить**, **Установить блокировку** and
  **Снять блокировку** operate on selected account rows from the top toolbar;
- account columns are resizable and movable; their layout is preserved between launches;
- account rows can be reordered by drag-and-drop and their order is stored in SQLite;
- added **Настройки -> Тема -> Системная / Светлая / Тёмная** using one application-wide Qt
  palette/theme layer so future standard controls inherit the selected theme automatically;
- added latest action amount, payment name, latest action date, offers and blocking columns;
- latest action data follows the legacy VBA 88-day expense scan across the same expense categories;
- **База оферов** mirrors the VBA offer catalog: offer ID/title/descriptions, inherited note
  (`оставить` / `удалить`) and numbers on which an offer was seen;
- **Доступные опции** accumulates unique options by `optionId` from
  `/api/options/v2/list?showVASP=false`, retaining all returned fields;
- number blocking follows the VBA mechanism: connect option
  `Q0L16QxY-nvN6dgAV04woA`; unblocking resolves the current **Блокировка номера** `optionId`
  and deletes that option;
- the proven v0.2.1 B2C authorization/session/CAPTCHA flow remains the auth foundation;
- explicit refresh-token renewal is still intentionally not implemented until a proven current
  B2C source of truth is available.

## Installation and updates

Windows distribution is one executable installer retained in the latest GitHub Release.

Current and future versions are `MegafonDesktop-Update-vX.Y.Z.exe`. An update installer is a
full payload: it upgrades an existing installation in place and can also perform a clean
installation when no older version is installed.

Program files: `%LOCALAPPDATA%\Programs\Megafon Desktop`

Application data: `%LOCALAPPDATA%\MegaFonDesktop`

Update installation does not delete application data, passwords, settings, table layout or saved
HTTP authorization. Uninstall removes both application-owned locations and application shortcuts.

## Development

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
megafon-desktop
```

## Data and secrets

Application data is kept under `%LOCALAPPDATA%\MegaFonDesktop` on Windows. Passwords and
serialized reusable HTTP authorization state are not stored in plaintext in SQLite: Windows DPAPI
encrypts them for the current Windows user.

## Research inputs

The implementation is based on:

1. the owner's legacy VBA automation;
2. fresh owner browser-network captures of the consumer personal cabinet;
3. current public reverse-engineered B2C implementations;
4. Qt/PySide6 native table, drag/drop and application palette facilities.

Browser tooling is a research instrument only; Megafon Desktop runtime remains HTTP-only.
