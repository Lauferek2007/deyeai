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
- logika ekonomiczna oparta o ceny importu i eksportu.

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
