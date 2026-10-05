# MegaFon Desktop

Native Windows desktop manager for **consumer** MegaFon accounts.

The project replaces a legacy Excel/VBA workflow with a maintainable application:

- multiple accounts in one local database;
- direct HTTP transport for known `api.megafon.ru/mlk/...` operations;
- browser/Playwright fallback when the internal API changes or interactive login is required;
- balances, tariff, services/options, expenses, forwarding and personal offers;
- owner-defined rules for keeping/rejecting personal offers;
- no browser extension and no B2B scope.

> The consumer MegaFon endpoints used by this project are internal, undocumented interfaces and
> may change without notice. Network behavior is therefore isolated behind transport interfaces.

## Current status

`v0.1.0` is the first installable Windows build: account storage, Windows DPAPI secret storage, a direct HTTP login/balance transport, refresh orchestration, native Qt account table and Playwright-based persistent-profile fallback groundwork.

The authoritative repository is `lvlaksim1/megafon-desktop`. The earlier `megafon-manager` repository is legacy/migration material only.

## Installation

Windows releases are published as executable installers in GitHub Releases.

- Initial installation: `MegafonDesktop-Setup-v0.1.0.exe`
- Future versions: `MegafonDesktop-Update-vX.Y.Z.exe`

Update installers use the same application identity and install directory, so they upgrade the installed application in place. See `docs/release.md`.

## Development

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
megafon-desktop
```

For the later Playwright fallback:

```powershell
pip install -e ".[browser]"
playwright install chromium
```

## Data and secrets

Application data is kept under `%LOCALAPPDATA%\MegaFonDesktop` on Windows. Passwords are not
stored in SQLite: Windows DPAPI encrypts them for the current Windows user.

## Research inputs

The implementation is based on three evidence sources:

1. the owner's working legacy VBA automation;
2. public open-source projects, especially `artyl/mbplugin` (MIT);
3. browser network logs supplied by the owner as MegaFon changes its cabinet.

See `docs/research/` for the maintained findings.
