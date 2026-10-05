# Megafon Desktop

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

`v0.1.1` is the current Windows build. It includes the v0.1.0 application vertical slice plus the
hardened update/uninstall and repository-retention policy.

The authoritative repository is `lvlaksim1/megafon-desktop`. The earlier `megafon-manager`
repository is legacy/migration material only.

## Installation and updates

Windows distribution is one executable installer retained in the latest GitHub Release.

- The initial public build was `MegafonDesktop-Setup-v0.1.0.exe`.
- Current and future versions are `MegafonDesktop-Update-vX.Y.Z.exe`.

An update installer is a full payload: it upgrades an existing installation in place and can also
perform a clean installation when no older version is installed.

Program files: `%LOCALAPPDATA%\Programs\Megafon Desktop`

Application data: `%LOCALAPPDATA%\MegaFonDesktop`

Uninstall removes both application-owned locations and application shortcuts. See
`docs/release.md`.

Release builds are not retained as GitHub Actions artifacts. After publishing a new release, older
releases/tags and residual Actions artifacts are removed automatically.

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
