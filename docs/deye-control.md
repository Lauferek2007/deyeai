# Deye Control Strategy

## Co wiemy

Deye/Sunsynk nie ma jednego "uniwersalnego" przełącznika typu:

- sprzedawaj do sieci,
- nie sprzedawaj,
- rozładuj baterię,
- ładuj baterię.

W praktyce sterowanie robi się kombinacją kilku nastaw:

- `solar_export`
- `use_timer`
- `grid_charge_enabled`
- `load_limit`
- `battery_max_charge_current`
- tryby programu czasowego typu `prog1_mode`
- w niektórych ścieżkach bezpośrednim zapisem rejestrów przez Solarman/Modbus

## Znane wzorce sterowania

Na podstawie dokumentacji i przykładów społeczności:

- sam slot TOU nie wystarczy, jeśli systemowy eksport jest wyłączony,
- `use_timer` musi być aktywne, aby programy czasowe sterowały zachowaniem,
- dla ładowania z sieci trzeba zwykle włączyć `grid_charge_enabled`,
- `Allow Export` pozwala zasilać odbiory i eksportować do sieci,
- `Zero Export` ogranicza eksport,
- `Essentials` ogranicza zasilanie do obwodów po stronie falownika,
- obniżenie `battery_max_charge_current` może celowo wypchnąć nadmiar PV do sieci zamiast ładować magazyn,
- `prog1_mode = Charge` może zostać użyte do nocnego ładowania z sieci.

Źródła:

- Solarman integration: local access plus service access for advanced users
- Deye/Sunsynk examples: automations using `load_limit`, `battery_max_charge_current`, `prog1_mode`

## Jak to łączymy w projekcie

Wspólny optimizer liczy wartość energii w baterii i wybiera scenariusz.

Dla Deye adapter ma tłumaczyć scenariusz na:

1. tryb nocny z eksportem lub bez eksportu,
2. ograniczenie albo otwarcie ładowania baterii,
3. nocne ładowanie z sieci przy taniej energii,
4. poranne przygotowanie miejsca na PV.

## Harmonogram 24h

Aktualna wersja projektu buduje też diagnostyczny plan godzinowy na najbliższe 24 godziny.

Tryby slotów:

- `grid_charge`
- `self_use`
- `preserve_headroom`
- `export_surplus`
- `export_battery`

Ten harmonogram nie ustawia jeszcze pełnego TOU schedule w każdym modelu Deye, ale daje wspólny plan decyzyjny, który będzie podstawą pod kolejną iterację wykonawczą.

## Pierwsze wykonanie TOU

Projekt potrafi już spróbować skompresować harmonogram 24h do maksymalnie trzech slotów TOU:

- `grid_charge`
- `export_battery`
- `export_surplus`

Jeśli w Home Assistant są dostępne encje:

- `prog1_time`, `prog1_mode`
- `prog2_time`, `prog2_mode`
- `prog3_time`, `prog3_mode`

adapter Deye spróbuje ustawić czas startu i tryb dla tych slotów.

Jeżeli są też dostępne:

- `solar_export`
- `use_timer`
- `grid_charge_enabled`

projekt spróbuje je przełączać zgodnie z planem.

To nadal jest wersja ostrożna:

- ustawia początek slotu i tryb,
- nie mapuje jeszcze wszystkich możliwych parametrów mocy i końca okna,
- wymaga potwierdzenia nazw opcji select dla konkretnej integracji i modelu.

## Ograniczenia

Nadal trzeba zweryfikować mapowanie sterowania na konkretnych modelach:

- SUN-xxK-SG04LP3
- SUN-xxK-SG01HP3
- inne warianty z różnymi loggerami i firmware

Nie każdy zestaw encji występuje w każdej integracji.
