# Manager plans

1. Keep `lvlaksim1/megafon-desktop` as the sole active product repository.
2. Treat B2C web-LK reverse traffic and current proven reverse implementations as protocol authority; ignore B2B and official/public MegaFon API documentation.
3. Keep runtime HTTP-only and manual-refresh-only.
4. Use dynamic frontend bootstrap, `sessionCheck`, one-session CAPTCHA login, immediate cookie persistence and account-identity validation as the auth baseline.
5. Await owner live verification of v0.2.1; if it fails, diagnose the exact server response before editing the protocol.
6. Research refresh-token renewal only from a proven current B2C source of truth. Do not use expiry experiments or speculative endpoints.
7. Resume remainders/services/expenses/tariff after auth live confirmation; keep mutations gated.
8. Use replay/contract tests based on redacted real-capture structures for future protocol changes.
9. Keep account deletion coupled to database, password and auth-state cleanup.
10. Publish each fixed version as an executable update installer; use the trusted PC Runner Gateway exact-SHA release task when hosted runners are unavailable.

## Актуальный план после выпуска v0.3.6 (приоритет над ранними пунктами)
1. Продолжать на основе Qt Widgets/QTableWidget и подтверждённой ветки `v0.3.6`; не восстанавливать отклонённый вариант QML без прямого решения владельца.
2. Проверить в реальном клиенте выделение диапазона, редактирование метки, Ctrl+F, порядок строк и столбцов, прокрутку и оформление.
3. Проверить восстановленный механизм персональных предложений по данным реального аккаунта, сохраняя ограничения на действия, влияющие на услуги и баланс.
4. Оставить обновление refresh-токена не реализованным до появления проверенного источника его действующего механизма; не проводить эксперименты с истечением срока токена.
5. Для следующих выпусков сохранять проверяемость сборки, единый актуальный выпуск и исполняемый установщик обновления.

Источник: `.context/current/state.md`, `.context/current/next.md`, `.context/handoffs/latest.md` (состояние после `v0.3.6`). Старые пункты о проверке v0.2.1 остаются историческими, а не более приоритетными.
