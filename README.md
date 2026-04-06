# Hybrid AI Energy Manager

Uniwersalna integracja Home Assistanta instalowana przez HACS do inteligentnego sterowania pracą falownika hybrydowego i magazynu energii.

Projekt ma robić cztery rzeczy:

- czytać prognozę produkcji PV,
- przewidywać zużycie budynku,
- wyliczać optymalny plan pracy baterii,
- wykonywać ten plan przez adapter konkretnego falownika.

Prognoza zużycia działa automatycznie i uczy się profilu budynku bez ręcznego trenowania:

- zapisuje historię zużycia per dzień tygodnia i godzina,
- buduje osobne profile dla poniedziałku, wtorku i tak dalej,
- po restarcie Home Assistanta zachowuje wyuczony profil,
- łączy profil tygodniowy z ostatnimi próbkami, żeby reagować też na bieżące odchylenia.

Mozna tez dodac reczne tygodniowe offsety jako korekte dla automatyki.
Przyklad:
`[{"day": 5, "start_hour": 10, "duration_hours": 5, "power_w": 11000, "label": "EV charging"}]`

Dodatkowo integracja ma tryb autodiscovery:

- automatyczne wykrywanie najpopularniejszych rodzin falowników,
- heurystyczne dopinanie encji dla nieznanego falownika,
- fallback do adaptera `generic`, gdy vendor nie zostanie wykryty jednoznacznie.

## Priorytet: Deye

Aktualnie projekt jest rozwijany przede wszystkim pod `Deye/Sunsynk`.

Obecny kierunek sterowania:

- `load_limit` do wyboru trybu `Essentials`, `Zero Export`, `Allow Export`,
- `battery_max_charge_current` do ograniczania lub otwierania ładowania,
- `prog1_mode` do nocnego ładowania z sieci przy słabej prognozie PV i taniej energii,
- logika ekonomiczna oparta o ceny importu i eksportu,
- diagnostyczny harmonogram 24h pokazujący plan `grid_charge`, `self_use`, `preserve_headroom`, `export_surplus` i `export_battery`,
- mapowanie harmonogramu na sloty TOU `program_1..6`, jeśli backend je wystawia.

Projekt nie zakłada jednej sztywnej listy encji.
Warstwa adaptera wybiera sciezke wykonania na podstawie capabilities backendu:

- jesli backend wystawia `work_mode`, sterowanie eksportem idzie przez `work_mode`,
- jesli wystawia osobny `export_surplus` albo `solar_export`, adapter uzyje switcha,
- jesli wystawia `time_of_use`, harmonogram aktywuje TOU przez select,
- jesli wystawia tylko programy `program_X_*`, adapter ustawia same sloty.

To jest właściwy kształt produktu jako `custom integration`, nie tylko add-on. Add-on może pojawić się później do cięższych obliczeń, ale rdzeń musi żyć w integracji HA.

## Kluczowy scenariusz

Jeżeli jutro rano i w ciągu dnia spodziewana jest wysoka produkcja PV, integracja ma celowo obniżyć SOC magazynu w nocy do bezpiecznego minimum, nawet rozładowując baterię na potrzeby domu albo eksportując energię do sieci, jeśli konfiguracja i taryfa to uzasadniają. Dzięki temu falownik ma wolną pojemność od rana.

## Założenia architektoniczne

- jeden wspólny silnik decyzyjny,
- osobne adaptery dla producentów i backendów,
- `dry-run` jako domyślny tryb startowy,
- maksymalne wykorzystanie już istniejących integracji HA.

## Pierwsze docelowe adaptery

- Deye / Solarman
- GoodWe
- Huawei Solar
- Generic Home Assistant entities

## Stan repo

Repo zawiera startowy szkielet:

- manifest HACS,
- custom integration,
- config flow,
- prosty silnik forecast + optimizer,
- adapter registry,
- autodiscovery adaptera i encji,
- dokumentację produktu i roadmapę.

## Lovelace card

Repo zawiera też uniwersalną kartę Lovelace dla tej integracji.
Instrukcja dodania i konfiguracji:

- [docs/lovelace-card.md](C:/Users/Biuro/Documents/Playground/ha-hybrid-ai-manager/docs/lovelace-card.md)
