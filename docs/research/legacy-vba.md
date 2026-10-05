# Legacy VBA functional map

The owner's supplied VBA is the primary behavioral specification for the initial consumer-LK
feature set. The original file is intentionally not committed because it may contain account-specific
values and historical experiments.

## Active flow observed

For each selected account the legacy workflow:

1. obtains/reuses an authenticated MegaFon session;
2. reads commercial/financial balance from `/mlk/api/balance/commercial`;
3. reads mobile balance from `/mlk/api/main/balance`;
4. checks current paid options;
5. examines expenses for the recent period and derives the latest paid action;
6. processes personal offers against a local allow/reject knowledge base;
7. disables a configured list of unwanted options;
8. discovers available options and records their metadata;
9. records the refresh date.

Additional implemented functions include tariff change, call-forwarding reset/set, option connect,
personal-offer activation/rejection and interest selection.

## First implementation endpoints

`v0.1` starts only with login and the two balance reads. Destructive or bill-affecting operations are
not enabled until their current request/response contracts are verified against fresh browser logs.
