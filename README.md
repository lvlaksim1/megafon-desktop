# Megafon Desktop

Native Windows desktop manager for **consumer** MegaFon accounts.

The project replaces a legacy Excel/VBA workflow with a maintainable application:

- multiple accounts in one local database;
- direct HTTP transport for known `api.megafon.ru/mlk/...` operations;
- persistent per-account HTTP authorization protected by Windows DPAPI;
- interactive CAPTCHA inside the desktop application;
- explicit manual refresh per account, selected accounts, or all accounts;
- balances, tariff, services/options, expenses, forwarding and personal offers;
- owner-defined rules for keeping/rejecting personal offers;
- no browser extension, no browser runtime dependency, and no B2B scope.

> The consumer MegaFon endpoints used by this project are internal, undocumented interfaces and
> may change without notice. Network behavior is therefore isolated behind transport interfaces.

## Current status

`v0.2.0` is the current Windows build.

The authoritative repository is `lvlaksim1/megafon-desktop`. The earlier `megafon-manager`
repository is legacy/migration material only.

### v0.2.0

- refresh is never started automatically when the program opens;
- each account has its own **Обновить** button;
- toolbar actions support **Обновить выбранные** and **Обновить всё**;
- successful HTTP authorization is preserved between program runs and update installs;
- when MegaFon returns CAPTCHA code `a211`, the JPEG from `/api/captcha/next` is displayed
  inside Megafon Desktop and the entered value is submitted to the same HTTP login flow;
- the runtime no longer depends on Playwright or an installed browser;
- application, executable shortcut and installer use the Megafon Desktop icon.

## Installation and updates

Windows distribution is one executable installer retained in the latest GitHub Release.

- The initial public build was `MegafonDesktop-Setup-v0.1.0.exe`.
- Current and future versions are `MegafonDesktop-Update-vX.Y.Z.exe`.

An update installer is a full payload: it upgrades an existing installation in place and can also
perform a clean installation when no older version is installed.

Program files: `%LOCALAPPDATA%\Programs\Megafon Desktop`

Application data: `%LOCALAPPDATA%\MegaFonDesktop`

Update installation does not delete application data, passwords, or saved HTTP authorization.
Uninstall removes both application-owned locations and application shortcuts. See
`docs/release.md`.

Release builds are not retained as GitHub Actions artifacts. After publishing a new release, older
releases/tags and residual Actions artifacts are removed automatically. CI/release pip caching is
also disabled to avoid repository Actions-cache growth.

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

The implementation is based on three evidence sources:

1. the owner's working legacy VBA automation;
2. public open-source projects, especially `artyl/mbplugin` (MIT);
3. browser network logs supplied by the owner strictly as research evidence for current MegaFon
   HTTP contracts.

See `docs/research/` for the maintained findings.
