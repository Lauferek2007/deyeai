# Hybrid AI Energy Manager

Uniwersalna integracja Home Assistanta instalowana przez HACS do inteligentnego sterowania pracą falownika hybrydowego i magazynu energii.

Projekt ma robić cztery rzeczy:

- czytać prognozę produkcji PV,
- przewidywać zużycie budynku,
- wyliczać optymalny plan pracy baterii,
- wykonywać ten plan przez adapter konkretnego falownika.

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
- dokumentację produktu i roadmapę.
