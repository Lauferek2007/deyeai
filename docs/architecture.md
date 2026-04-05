# Architecture

## Dlaczego custom integration

To rozwiązanie powinno być przede wszystkim integracją HACS, bo wtedy może:

- rejestrować encje, usługi i diagnostykę w Home Assistant,
- czytać istniejące sensory i integracje,
- współpracować z Energy Dashboard,
- korzystać z obecnych integracji falowników zamiast przepisywać wszystko od zera.

## Warstwy systemu

1. `inputs`
2. `forecast`
3. `optimizer`
4. `adapters`

## Inputs

Minimalne dane wejściowe:

- SOC baterii,
- moc domu,
- moc PV,
- moc importu/eksportu,
- pojemność użyteczna baterii.

Dodatkowe dane:

- cena zakupu energii,
- cena sprzedaży / opust / wartość eksportu,
- prognoza PV,
- kalendarz i sygnały obecności,
- duże odbiory sterowalne.

## Forecast

Pierwsza wersja nie powinna udawać rozbudowanego AI. Praktyczny start:

- prognoza PV z `Forecast.Solar`, `Solcast` albo innej encji HA,
- prognoza zużycia z historii Home Assistanta,
- baseline per godzina tygodnia,
- korekta na ostatnie dni i ostatnie godziny.

## Optimizer

Cel optymalizacji powinien równoważyć:

- przygotowanie miejsca na jutrzejszą produkcję,
- ograniczenie drogiego importu,
- unikanie bezsensownych cykli baterii,
- wykorzystanie nocnego eksportu tam, gdzie to ma sens,
- zachowanie rezerwy bezpieczeństwa.

## Adaptery

Uniwersalny może być mózg systemu, ale nie mapowanie komend falownika.

Dlatego:

- jeden wspólny format decyzji,
- osobne adaptery per backend lub vendor,
- osobne bezpieczeństwo i mapowanie komend per adapter.

## Tryby pracy

- `dry_run`
- `advisory`
- `active`

Domyślnie projekt powinien startować w `dry_run`.
