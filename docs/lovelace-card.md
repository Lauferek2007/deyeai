# Hybrid AI Lovelace Card

Integracja wystawia frontend karty pod dwoma adresami:

- `/api/hybrid_ai/static/hybrid-ai-card.js`
- `/hybrid_ai-static/hybrid-ai-card.js`

## Dodanie zasobu

W `Home Assistant`:

1. `Ustawienia -> Dashboardy -> Zasoby`
2. dodaj resource:
   - URL: `/api/hybrid_ai/static/hybrid-ai-card.js`
   - type: `JavaScript Module`

Nowy alias `/hybrid_ai-static/hybrid-ai-card.js` tez dziala, ale stary adres jest
bezpieczniejszy dla juz zainstalowanych dashboardow.

## Dodanie karty

Najprostsza konfiguracja:

```yaml
type: custom:hybrid-ai-card
title: Hybrid AI
```

Przyklad z pelniejszymi ustawieniami:

```yaml
type: custom:hybrid-ai-card
title: Hybrid AI
show_tou_plan: true
show_actions: true
show_hourly_schedule: true
show_price_context: true
compact: false
```

Jesli karta nie znajdzie glownej encji automatycznie, mozna podac ja recznie:

```yaml
type: custom:hybrid-ai-card
entity: sensor.hybrid_ai_energy_manager_plan_summary
title: Hybrid AI
```

## Co pokazuje karta

- biezace podsumowanie planu,
- adapter i stan `dry_run/write mode`,
- aktywny tryb z planu godzinowego,
- najblizszy slot TOU,
- forecast PV, load i surplus,
- docelowy poranny `SOC`,
- forecast confidence,
- kontekst cenowy,
- akcje adaptera,
- podglad planu godzinowego,
- przycisk `Przelicz plan`.
