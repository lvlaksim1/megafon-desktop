# Manager intentions and commitments

## Active

1. **M1 v0.2.1 live authorization verification — active.** The evidence-backed B2C HTTP auth repair is implemented and released; next gate is owner-side live behavior.
2. **M2 persistent authorization — active.** Keep per-account DPAPI auth state across restarts/updates while preserving manual-refresh-only UX.
3. **M3 refresh-token source research — active.** Find a proven current B2C source of truth. No expiry experiments; no guessed refresh endpoint or rotation rule.
4. **M4 B2C read-model expansion — accepted but sequenced after live auth confirmation.** Remainders, services, tariff and expenses follow.
5. **M5 controlled mutations — accepted but gated.** Bill-affecting changes remain disabled until current contracts are independently verified.
6. **M6 update delivery — active.** Every post-initial version is an executable `MegafonDesktop-Update-vX.Y.Z.exe` preserving app data.

## Completed

- Initial native Windows delivery and update installer pipeline.
- Fresh B2C CAPTCHA/login capture analysis and public-source cross-check.
- Dynamic X-Cabinet frontend bootstrap/sessionCheck auth repair.
- CAPTCHA continuation and immediate auth persistence.
- Account deletion and requested toolbar cleanup.
- v0.2.1 Windows build/publication via trusted PC Runner Gateway.

Completion requires repository evidence plus relevant tests/runtime verification; a plan change does not cancel active commitments.

## Актуальное продолжение после v0.3.6
- **M7 — активная пользовательская приёмка v0.3.6.** Проверить на реальных аккаунтах устойчивость Qt Widgets, порядок строк и столбцов, выделение, редактирование `Метка`, поиск, прокрутку и тёмную тему. Факт публикации и успешной сборки не закрывает пользовательскую приёмку.
- **M8 — активная проверка восстановленных персональных предложений.** Проверить сохранение/отклонение, неизвестные предложения и связанные опции в реальном клиенте.
- **M3 — сохраняется.** Обновление refresh-токена остаётся неподтверждённым и не реализуется по предположению.
- source: `.context/current/next.md`, `.context/current/state.md`, GitHub Release `v0.3.6`
- authority: verified-repository; прежние поручения владельца, уже сохранённые в состоянии проекта

Пункты M1–M6 выше остаются историей и открытыми обязательствами там, где не зарегистрировано их завершение. Более ранний план пользовательской проверки v0.2.1 не отменяет актуальную проверку v0.3.6.
