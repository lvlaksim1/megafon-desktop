# Manager intentions and commitments

## Active

1. **M1 B2C HTTP authorization repair — highest priority.** Replace the simplified v0.2.0 login with the verified consumer web-LK bootstrap/sessionCheck/CAPTCHA/cookie lifecycle. No browser runtime.
2. **M2 persistent authorization — active.** Persist per-account auth state with Windows DPAPI across application restarts and update installers, without any automatic network refresh at startup.
3. **M3 refresh-token verification — active.** Determine the exact renewal behavior of the long-lived `X-Cabinet-Refresh-Token` after the short access/id tokens expire; do not invent an endpoint or rotation rule without evidence.
4. **M4 UI corrections — active.** Add account deletion; remove **Обновить выбранные** and the toolbar logo beside **Добавить номер**; retain per-account **Обновить**, **Обновить всё**, and the application/system icon.
5. **M5 B2C read-model expansion — accepted but sequenced after auth repair.** Remainders, services, tariff and expenses follow only after the auth foundation is verified.
6. **M6 controlled mutations — accepted but gated.** Bill-affecting changes remain disabled until current contracts are independently verified.
7. **M7 update delivery — active.** Every post-initial version is delivered as an executable `MegafonDesktop-Update-vX.Y.Z.exe` installer preserving app data.

## Completed

- Initial native Windows delivery and installer/update pipeline.
- Fresh B2C CAPTCHA/login capture analysis and cross-check against current public reverse-engineered implementations.

Completion requires repository evidence plus relevant tests/runtime verification; a plan change does not cancel active commitments.
