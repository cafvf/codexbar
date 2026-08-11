# UC-1711 — Native indicator fails but Qt fallback works

## Flow
1. Native helper becomes unhealthy or unavailable.
2. CodexBar activates Qt fallback.
3. System Health records native degradation/fallback evidence.

## Expected
Overall application remains healthy when the fallback is operational.
