# Hybrid AI Lovelace Card

Integracja wystawia własny frontend pod adresem:

- `/api/hybrid_ai/static/hybrid-ai-card.js`

## Dodanie zasobu

W `Home Assistant`:

1. `Ustawienia -> Dashboardy -> Zasoby`
2. dodaj resource:
   - URL: `/api/hybrid_ai/static/hybrid-ai-card.js`
   - type: `JavaScript Module`

## Dodanie karty

Najprostsza konfiguracja:

```yaml
type: custom:hybrid-ai-card
title: Hybrid AI
```

Przykład z pełniejszymi ustawieniami:

```yaml
type: custom:hybrid-ai-card
title: Hybrid AI
show_tou_plan: true
show_actions: true
show_hourly_schedule: true
show_price_context: true
compact: false
```

Jeśli karta nie znajdzie głównej encji automatycznie, można podać ją ręcznie:

```yaml
type: custom:hybrid-ai-card
entity: sensor.hybrid_ai_energy_manager_plan_summary
title: Hybrid AI
```

## Co pokazuje karta

- bieżące podsumowanie planu,
- adapter i stan `dry_run/write mode`,
- aktywny tryb z planu godzinowego,
- najbliższy slot TOU,
- forecast PV, load i surplus,
- docelowy poranny `SOC`,
- forecast confidence,
- kontekst cenowy,
- akcje adaptera,
- podgląd planu godzinowego,
- przycisk `Przelicz plan`.
