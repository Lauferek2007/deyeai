const CARD_TYPE = "hybrid-ai-card";
const DEFAULT_CONFIG = {
  title: "Hybrid AI",
  show_settings: true,
  show_tou_plan: true,
  show_actions: true,
  show_hourly_schedule: true,
  show_price_context: true,
  show_chart: true,
  show_discovery: true,
  compact: false,
};

const DISPLAY_LABELS = {
  unknown: "nieznane",
  generic: "ogolny",
  deye: "Deye",
  solarman: "Solarman",
  huawei: "Huawei",
  goodwe: "GoodWe",
  safe: "bezpieczny",
  active: "aktywny",
  done: "wykonano",
  queued: "w kolejce",
  "dry-run": "na sucho",
  self_use: "Autokonsumpcja",
  export_surplus: "Eksport nadwyzki",
  export_battery: "Eksport z baterii",
  preserve_headroom: "Zachowaj miejsce",
  grid_charge: "Ladowanie z sieci",
  set_target_morning_soc: "Ustaw poranny SOC",
  allow_overnight_discharge: "Zezwol na nocne rozladowanie",
  allow_export_discharge: "Zezwol na eksport z baterii",
  hold_reserve: "Zachowaj rezerwe",
  deye_enable_use_timer: "Wlacz harmonogram TOU",
  deye_set_target_morning_soc: "Ustaw poranny SOC",
  deye_set_battery_charge_current: "Ustaw prad ladowania",
  deye_enable_system_export: "Wlacz eksport do sieci",
  deye_allow_export_discharge: "Zezwol na eksport z baterii",
  deye_enable_grid_charge: "Wlacz ladowanie z sieci",
  deye_force_grid_charge: "Wymus ladowanie z sieci",
  deye_prepare_grid_charge_window: "Przygotuj okno ladowania",
  deye_hold_strategy: "Zachowaj energie w baterii",
  deye_limit_early_pv_battery_charging: "Ogranicz poranne ladowanie baterii",
  deye_apply_tou_schedule: "Zastosuj harmonogram TOU",
  entity: "encja prognozy PV",
  weather_hourly_service: "pogoda godzinowa",
  weather_daily_service: "pogoda dzienna",
  weather_state: "stan pogody",
  manual_fallback: "pogoda plus reczny limit",
  "entity + cap": "encja PV plus limit",
  entity_keywords: "slowa kluczowe encji",
  fallback: "tryb zapasowy",
};

class HybridAiCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = { ...DEFAULT_CONFIG };
  }

  static getConfigElement() {
    return document.createElement("hybrid-ai-card-editor");
  }

  static getStubConfig() {
    return { title: "Hybrid AI" };
  }

  setConfig(config) {
    this._config = { ...DEFAULT_CONFIG, ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return this._config.compact ? 8 : 12;
  }

  _findEntity() {
    if (!this._hass) {
      return undefined;
    }
    if (this._config.entity) {
      return this._config.entity;
    }

    const preferred = Object.keys(this._hass.states).find((entityId) => {
      if (!entityId.startsWith("sensor.") || !entityId.endsWith("_plan_summary")) {
        return false;
      }
      const state = this._hass.states[entityId];
      return Array.isArray(state?.attributes?.hourly_schedule);
    });

    if (preferred) {
      return preferred;
    }

    return Object.keys(this._hass.states).find(
      (entityId) => entityId.startsWith("sensor.") && entityId.endsWith("_plan_summary"),
    );
  }

  _render() {
    if (!this.shadowRoot) {
      return;
    }

    const entityId = this._findEntity();
    const stateObj = entityId ? this._hass?.states?.[entityId] : undefined;

    if (!stateObj) {
      this.shadowRoot.innerHTML = `
        <ha-card header="${this._config.title}">
          ${this._style()}
          <div class="shell">
            <div class="empty-state">
              <div class="empty-title">Nie znaleziono encji Hybrid AI</div>
              <div class="empty-copy">
                Najpierw dodaj integracje albo wskaz recznie glowna encje w ustawieniach karty.
              </div>
            </div>
          </div>
        </ha-card>
      `;
      return;
    }

    const attrs = stateObj.attributes || {};
    const hourly = Array.isArray(attrs.hourly_schedule) ? attrs.hourly_schedule : [];
    const touPlan = Array.isArray(attrs.tou_plan) ? attrs.tou_plan : [];
    const actions = Array.isArray(attrs.adapter_actions) ? attrs.adapter_actions : [];
    const prices = attrs.price_context || {};
    const settings = attrs.settings || {};
    const discovery = attrs.discovery || {};
    const forecastMeta = attrs.forecast_details?.solar || attrs.forecast_details || {};
    const activeMode = hourly[0]?.mode || "self_use";
    const nextTou = touPlan[0]
      ? `P${touPlan[0].program} ${this._hour(touPlan[0].start_hour)}-${this._hour(touPlan[0].end_hour)}`
      : "Brak aktywnego okna";

    this.shadowRoot.innerHTML = `
      <ha-card header="${this._config.title}">
        ${this._style()}
        <div class="shell ${this._config.compact ? "compact" : ""}">
          ${this._renderHero(stateObj, attrs, activeMode, nextTou, forecastMeta)}
          ${this._renderActionBar()}
          ${this._config.show_chart ? this._renderChart(hourly, attrs, forecastMeta) : ""}
          <div class="grid-panels">
            ${this._config.show_settings ? this._renderSettings(settings, forecastMeta) : ""}
            ${this._config.show_discovery ? this._renderDiscovery(discovery) : ""}
            ${this._config.show_price_context ? this._renderPrices(prices) : ""}
            ${this._config.show_tou_plan ? this._renderTou(touPlan) : ""}
            ${this._config.show_actions ? this._renderActions(actions) : ""}
            ${this._config.show_hourly_schedule ? this._renderHourly(hourly) : ""}
          </div>
        </div>
      </ha-card>
    `;

    this._wireActions();
  }

  _wireActions() {
    const runButton = this.shadowRoot.getElementById("hybrid-ai-run");
    if (runButton) {
      runButton.onclick = () => this._hass.callService("hybrid_ai", "run_optimization", {});
    }

    const discoverButton = this.shadowRoot.getElementById("hybrid-ai-discover");
    if (discoverButton) {
      discoverButton.onclick = () => this._hass.callService("hybrid_ai", "discover_entities", {});
    }

    const entityButton = this.shadowRoot.getElementById("hybrid-ai-more-info");
    if (entityButton) {
      entityButton.onclick = () =>
        this.dispatchEvent(
          new CustomEvent("hass-more-info", {
            detail: { entityId: this._findEntity() },
            bubbles: true,
            composed: true,
          }),
        );
    }
  }

  _renderHero(stateObj, attrs, activeMode, nextTou, forecastMeta) {
    const summary = stateObj.state || "No plan";
    const chips = [
      this._badge("Adapter", this._labelize(attrs.adapter || "unknown")),
      this._badge(
        attrs.dry_run ? "Tryb" : "Tryb",
        attrs.dry_run ? "bezpieczny" : "aktywny",
        attrs.dry_run ? "amber" : "teal",
      ),
      this._badge("Biezacy plan", this._labelize(activeMode)),
      this._badge("Nastepne TOU", nextTou),
    ].join("");

    return `
      <section class="hero">
        <div class="hero-copy">
          <div class="eyebrow">Inteligentne planowanie pracy baterii i falownika</div>
          <div class="summary">${summary}</div>
          <div class="badge-row">${chips}</div>
        </div>
        <div class="hero-stats">
          ${this._metric("PV na 24h", this._formatNumber(attrs.forecast_solar_kwh, "kWh"), "Spodziewana produkcja energii z instalacji PV")}
          ${this._metric("Zuzycie na 24h", this._formatNumber(attrs.forecast_load_kwh, "kWh"), "Przewidywane zuzycie budynku")}
          ${this._metric("Nadwyzka", this._formatNumber(attrs.expected_surplus_kwh, "kWh"), "Energia do eksportu albo zwolnienia miejsca w baterii")}
          ${this._metric("Poranny SOC", this._formatNumber(attrs.target_morning_soc, "%"), "Docelowy poziom naladowania baterii rano")}
          ${this._metric("Pewnosc", this._formatPercent(attrs.forecast_confidence), "Jak pewna jest obecna prognoza")}
          ${this._metric("Zrodlo PV", this._shortForecastSource(forecastMeta), "Skad integracja bierze prognoze PV")}
        </div>
      </section>
    `;
  }

  _renderActionBar() {
    return `
      <section class="panel actions-panel">
        <div class="panel-title">Szybkie akcje</div>
        <div class="action-buttons">
          <button id="hybrid-ai-run" class="action-button action-primary">
            <span class="action-icon">+</span>
            <span>
              <strong>Przelicz plan</strong>
              <small>Przelicza prognozy, ceny i plan pracy baterii na nowo.</small>
            </span>
          </button>
          <button id="hybrid-ai-discover" class="action-button action-secondary">
            <span class="action-icon">?</span>
            <span>
              <strong>Autowykrywanie</strong>
              <small>Skanuje encje Home Assistanta i probuje ponownie dopasowac falownik, pogode i ceny.</small>
            </span>
          </button>
          <button id="hybrid-ai-more-info" class="action-button action-ghost">
            <span class="action-icon">i</span>
            <span>
              <strong>Szczegoly encji</strong>
              <small>Otwiera glowna encje diagnostyczna integracji Hybrid AI.</small>
            </span>
          </button>
        </div>
      </section>
    `;
  }

  _renderChart(hourly, attrs, forecastMeta) {
    const series = hourly.slice(0, this._config.compact ? 12 : 24);
    if (!series.length) {
      return `
        <section class="panel chart-panel">
          <div class="panel-title">Wykres PV i zuzycia</div>
          <div class="muted">Brak godzinowego planu do wyswietlenia.</div>
        </section>
      `;
    }

    const chart = this._buildChart(series);
    const solarSource = forecastMeta?.method ? `${forecastMeta.method}` : this._shortForecastSource(forecastMeta);
    const productionHint =
      Number(attrs.forecast_solar_kwh) > 0
        ? `${this._formatNumber(attrs.forecast_solar_kwh, "kWh")} przewidywanej produkcji`
        : "Brak prognozy PV";

    return `
      <section class="panel chart-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">Wykres PV i zuzycia</div>
            <div class="panel-subtitle">${productionHint}, zrodlo: ${solarSource}</div>
          </div>
          <div class="legend">
            <span class="legend-item"><span class="legend-swatch pv"></span>PV</span>
            <span class="legend-item"><span class="legend-swatch load"></span>Zuzycie</span>
          </div>
        </div>
        <div class="chart-wrap">${chart}</div>
      </section>
    `;
  }

  _buildChart(series) {
    const width = 660;
    const height = 220;
    const left = 24;
    const right = 14;
    const top = 12;
    const bottom = 28;
    const innerWidth = width - left - right;
    const innerHeight = height - top - bottom;
    const maxValue = Math.max(
      1,
      ...series.map((item) => Number(item.expected_pv_kwh || 0)),
      ...series.map((item) => Number(item.expected_load_kwh || 0)),
    );

    const xForIndex = (index) =>
      left + (series.length === 1 ? innerWidth / 2 : (index * innerWidth) / (series.length - 1));
    const yForValue = (value) => top + innerHeight - (Math.max(value, 0) / maxValue) * innerHeight;

    const pvPoints = series
      .map((item, index) => `${xForIndex(index).toFixed(2)},${yForValue(Number(item.expected_pv_kwh || 0)).toFixed(2)}`)
      .join(" ");
    const loadPoints = series
      .map((item, index) => `${xForIndex(index).toFixed(2)},${yForValue(Number(item.expected_load_kwh || 0)).toFixed(2)}`)
      .join(" ");

    const pvArea = [
      `${xForIndex(0).toFixed(2)},${(top + innerHeight).toFixed(2)}`,
      pvPoints,
      `${xForIndex(series.length - 1).toFixed(2)},${(top + innerHeight).toFixed(2)}`,
    ].join(" ");

    const gridLines = [0.25, 0.5, 0.75, 1]
      .map((ratio) => {
        const y = top + innerHeight - innerHeight * ratio;
        const value = (maxValue * ratio).toFixed(1);
        return `
          <line x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" class="grid-line"></line>
          <text x="4" y="${y + 4}" class="axis-label">${value}</text>
        `;
      })
      .join("");

    const labels = series
      .map((item, index) => {
        if (index !== 0 && index !== series.length - 1 && index % 4 !== 0) {
          return "";
        }
        const date = new Date(item.start);
        const label = Number.isNaN(date.getTime())
          ? `${index}`
          : `${String(date.getHours()).padStart(2, "0")}:00`;
        return `<text x="${xForIndex(index)}" y="${height - 6}" text-anchor="middle" class="axis-label">${label}</text>`;
      })
      .join("");

    return `
      <svg viewBox="0 0 ${width} ${height}" class="chart" role="img" aria-label="PV and load forecast chart">
        <defs>
          <linearGradient id="hybrid-ai-pv-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="rgba(248, 181, 0, 0.65)"></stop>
            <stop offset="100%" stop-color="rgba(248, 181, 0, 0.04)"></stop>
          </linearGradient>
        </defs>
        ${gridLines}
        <polyline points="${pvArea}" class="pv-area"></polyline>
        <polyline points="${pvPoints}" class="pv-line"></polyline>
        <polyline points="${loadPoints}" class="load-line"></polyline>
        ${labels}
      </svg>
    `;
  }

  _renderSettings(settings, forecastMeta) {
    const maxDailyPv =
      Number(settings.manual_max_daily_pv_kwh || 0) > 0
        ? this._formatNumber(settings.manual_max_daily_pv_kwh, "kWh")
        : "nie ustawiono";
    return `
      <section class="panel">
        <div class="panel-title">Ustawienia planera</div>
        <div class="fact-grid">
          ${this._fact("Autowykrywanie", settings.auto_discovery ? "wlaczone" : "wylaczone")}
          ${this._fact("Tryb zapisu", settings.enable_write_mode ? "wlaczony" : "wylaczony")}
          ${this._fact("Min SOC", this._formatNumber(settings.min_soc, "%"))}
          ${this._fact("Max SOC", this._formatNumber(settings.max_soc, "%"))}
          ${this._fact("Eksport", settings.export_allowed ? "tak" : "nie")}
          ${this._fact("Ladowanie z sieci", settings.grid_charge_allowed ? "tak" : "nie")}
          ${this._fact("Koszt cyklu", this._formatNumber(settings.battery_cycle_cost, ""))}
          ${this._fact("Odswiezanie", this._formatNumber(settings.update_interval_minutes, "min"))}
          ${this._fact("Maks. PV na dobe", maxDailyPv)}
          ${this._fact("Encja pogody", settings.weather_entity || "auto / brak")}
          ${this._fact("Encja prognozy PV", settings.solar_forecast_entity || "auto / brak")}
          ${this._fact("Metoda prognozy", this._shortForecastSource(forecastMeta))}
        </div>
      </section>
    `;
  }

  _renderDiscovery(discovery) {
    const notes = Array.isArray(discovery.notes) ? discovery.notes : [];
    const discovered = [
      this._fact("Adapter", this._labelize(discovery.adapter || "unknown")),
      this._fact("Pewnosc", this._formatPercent(discovery.confidence || 0)),
      this._fact("Dopasowanie", this._labelize(discovery.matched_by || "unknown")),
      this._fact("SOC baterii", this._shortEntity(discovery.battery_soc_entity)),
      this._fact("Moc zuzycia", this._shortEntity(discovery.load_power_entity)),
      this._fact("Moc PV", this._shortEntity(discovery.pv_power_entity)),
      this._fact("Moc sieci", this._shortEntity(discovery.grid_power_entity)),
      this._fact("Pogoda", this._shortEntity(discovery.weather_entity)),
      this._fact("Prognoza PV", this._shortEntity(discovery.solar_forecast_entity)),
      this._fact("Tryb pracy", this._shortEntity(discovery.deye_work_mode_entity)),
    ].join("");

    const notesBlock = notes.length
      ? `<div class="notice-list">${notes.map((item) => `<div class="notice-item">${item}</div>`).join("")}</div>`
      : `<div class="muted">Brak uwag z autowykrywania.</div>`;

    return `
      <section class="panel">
        <div class="panel-title">Status autowykrywania</div>
        <div class="fact-grid">${discovered}</div>
        ${notesBlock}
      </section>
    `;
  }

  _renderPrices(prices) {
    return `
      <section class="panel">
        <div class="panel-title">Kontekst cenowy</div>
        <div class="fact-grid">
          ${this._fact("Sredni zakup", this._formatNumber(prices.avg_import_price, ""))}
          ${this._fact("Srednia sprzedaz", this._formatNumber(prices.avg_export_price, ""))}
          ${this._fact("Najnizszy zakup", this._formatNumber(prices.cheapest_import_price, ""))}
          ${this._fact("Najlepsza sprzedaz", this._formatNumber(prices.highest_export_price, ""))}
        </div>
      </section>
    `;
  }

  _renderTou(items) {
    const content = items.length
      ? items
          .map(
            (item) => `
              <div class="slot-card">
                <div class="slot-top">
                  <span class="slot-program">P${item.program}</span>
                  <span class="slot-mode">${this._labelize(item.mode)}</span>
                </div>
                <div class="slot-hours">${this._hour(item.start_hour)}-${this._hour(item.end_hour)}</div>
                <div class="slot-label">${item.label || this._labelize(item.mode)}</div>
              </div>
            `,
          )
          .join("")
      : `<div class="muted">Brak aktywnych okien TOU.</div>`;

    return `
      <section class="panel">
        <div class="panel-title">Okna TOU</div>
        <div class="slot-grid">${content}</div>
      </section>
    `;
  }

  _renderActions(items) {
    const content = items.length
      ? items
          .map(
            (item) => `
              <div class="action-row">
                <div>
                  <div class="action-name">${this._labelize(item.action)}</div>
                  <div class="action-reason">${item.reason || "Brak uzasadnienia."}</div>
                </div>
                <div class="action-state">${item.executed ? "wykonano" : item.dry_run ? "na sucho" : "w kolejce"}</div>
              </div>
            `,
          )
          .join("")
      : `<div class="muted">Brak zaplanowanych akcji adaptera.</div>`;

    return `
      <section class="panel panel-wide">
        <div class="panel-title">Zaplanowane akcje adaptera</div>
        <div class="stack-list">${content}</div>
      </section>
    `;
  }

  _renderHourly(items) {
    const preview = items.slice(0, this._config.compact ? 8 : 12);
    const content = preview.length
      ? preview
          .map(
            (item) => `
              <div class="hour-row">
                <div class="hour-time">${this._formatHourLabel(item.start)}</div>
                <div class="hour-mode">${this._labelize(item.mode)}</div>
                <div class="hour-flow">${this._formatNumber(item.expected_pv_kwh, "kWh")} PV</div>
                <div class="hour-flow">${this._formatNumber(item.expected_load_kwh, "kWh")} zuzycie</div>
              </div>
            `,
          )
          .join("")
      : `<div class="muted">Brak planu godzinowego.</div>`;

    return `
      <section class="panel panel-wide">
        <div class="panel-title">Najblizszy plan godzinowy</div>
        <div class="stack-list">${content}</div>
      </section>
    `;
  }

  _metric(label, value, helpText) {
    return `
      <div class="metric-card">
        <div class="metric-label">${label}</div>
        <div class="metric-value">${value}</div>
        <div class="metric-help">${helpText}</div>
      </div>
    `;
  }

  _fact(label, value) {
    return `
      <div class="fact-card">
        <div class="fact-label">${label}</div>
        <div class="fact-value">${value}</div>
      </div>
    `;
  }

  _badge(label, value, tone = "ink") {
    return `
      <span class="badge badge-${tone}">
        <strong>${label}</strong>
        <span>${value}</span>
      </span>
    `;
  }

  _labelize(value) {
    if (value === undefined || value === null || value === "") {
      return "brak";
    }
    const normalized = String(value);
    return DISPLAY_LABELS[normalized] || normalized.replace(/_/g, " ");
  }

  _shortForecastSource(meta) {
    if (!meta || typeof meta !== "object") {
      return "nieznane";
    }
    if (meta.capped_by_manual_max) {
      return this._labelize("entity + cap");
    }
    if (meta.method) {
      return this._labelize(meta.method);
    }
    return meta.source || "nieznane";
  }

  _shortEntity(entityId) {
    if (!entityId) {
      return "nie przypisano";
    }
    return String(entityId).length > 34 ? `...${String(entityId).slice(-34)}` : String(entityId);
  }

  _formatNumber(value, suffix) {
    if (value === undefined || value === null || value === "") {
      return "brak";
    }
    const normalized = Number(value);
    if (Number.isNaN(normalized)) {
      return `${value}${suffix ? ` ${suffix}` : ""}`;
    }
    const precision = Math.abs(normalized) >= 100 ? 0 : 2;
    return `${normalized.toFixed(precision)}${suffix ? ` ${suffix}` : ""}`;
  }

  _formatPercent(value) {
    if (value === undefined || value === null || value === "") {
      return "brak";
    }
    return `${(Number(value) * 100).toFixed(0)} %`;
  }

  _hour(value) {
    return `${String(Number(value)).padStart(2, "0")}:00`;
  }

  _formatHourLabel(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString([], {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  _style() {
    return `
      <style>
        :host {
          --hybrid-ink: #0f172a;
          --hybrid-amber: #f59e0b;
          --hybrid-gold: #facc15;
          --hybrid-teal: #0f766e;
          --hybrid-mint: #34d399;
        }
        ha-card {
          overflow: hidden;
        }
        .shell {
          padding: 18px;
          display: grid;
          gap: 16px;
          background:
            radial-gradient(circle at top right, rgba(250, 204, 21, 0.12), transparent 32%),
            radial-gradient(circle at bottom left, rgba(52, 211, 153, 0.10), transparent 24%);
        }
        .shell.compact {
          gap: 12px;
          padding: 14px;
        }
        .hero {
          display: grid;
          gap: 16px;
          grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
          padding: 18px;
          border-radius: 22px;
          background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(15, 118, 110, 0.92));
          color: white;
          box-shadow: 0 16px 44px rgba(15, 23, 42, 0.28);
        }
        .eyebrow {
          font-size: 0.72rem;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          opacity: 0.7;
        }
        .summary {
          margin-top: 10px;
          font-size: 1.18rem;
          line-height: 1.55;
          max-width: 52rem;
        }
        .badge-row {
          margin-top: 14px;
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 7px 10px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.1);
          font-size: 0.82rem;
        }
        .badge strong {
          opacity: 0.78;
        }
        .badge-amber {
          background: rgba(245, 158, 11, 0.18);
        }
        .badge-teal {
          background: rgba(52, 211, 153, 0.16);
        }
        .hero-stats {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
        }
        .metric-card,
        .panel {
          border-radius: 18px;
          padding: 14px;
        }
        .metric-card {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
        }
        .metric-label,
        .fact-label {
          font-size: 0.78rem;
          opacity: 1;
          color: rgba(15, 23, 42, 0.68);
        }
        .metric-value {
          margin-top: 8px;
          font-size: 1.28rem;
          font-weight: 700;
        }
        .metric-help {
          margin-top: 6px;
          font-size: 0.75rem;
          opacity: 0.68;
          line-height: 1.45;
        }
        .panel {
          background: rgba(255, 255, 255, 0.86);
          border: 1px solid rgba(148, 163, 184, 0.18);
          box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
          display: grid;
          gap: 12px;
        }
        .panel-wide {
          grid-column: 1 / -1;
        }
        .panel-title {
          font-size: 0.98rem;
          font-weight: 700;
          color: var(--hybrid-ink);
        }
        .panel-subtitle {
          margin-top: 4px;
          font-size: 0.82rem;
          color: rgba(15, 23, 42, 0.64);
        }
        .panel-header,
        .slot-top,
        .action-row {
          display: flex;
          justify-content: space-between;
          gap: 12px;
        }
        .action-buttons,
        .grid-panels,
        .fact-grid,
        .slot-grid,
        .stack-list {
          display: grid;
          gap: 10px;
        }
        .action-buttons {
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        }
        .grid-panels {
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 14px;
        }
        .fact-grid,
        .slot-grid {
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        }
        .action-button {
          border: 0;
          border-radius: 18px;
          padding: 14px 16px;
          display: flex;
          gap: 12px;
          align-items: flex-start;
          cursor: pointer;
          text-align: left;
          font: inherit;
        }
        .action-button strong {
          display: block;
          font-size: 0.94rem;
        }
        .action-button small {
          display: block;
          margin-top: 4px;
          opacity: 0.72;
          line-height: 1.45;
        }
        .action-primary {
          color: white;
          background: linear-gradient(135deg, #dc6803, #0f766e);
        }
        .action-secondary {
          color: var(--hybrid-ink);
          background: linear-gradient(135deg, rgba(250, 204, 21, 0.2), rgba(255, 255, 255, 0.98));
        }
        .action-ghost {
          color: var(--hybrid-ink);
          background: rgba(241, 245, 249, 0.92);
        }
        .action-icon {
          min-width: 34px;
          height: 34px;
          border-radius: 12px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.16);
          font-weight: 700;
        }
        .chart-wrap,
        .fact-card,
        .slot-card,
        .action-row,
        .hour-row,
        .notice-item,
        .empty-state {
          border-radius: 16px;
          background: rgba(248, 250, 252, 0.96);
          border: 1px solid rgba(226, 232, 240, 0.9);
        }
        .chart-wrap {
          padding: 8px 8px 2px;
        }
        .chart {
          width: 100%;
          height: auto;
          display: block;
        }
        .grid-line {
          stroke: rgba(148, 163, 184, 0.22);
          stroke-width: 1;
        }
        .axis-label {
          fill: rgba(71, 85, 105, 0.84);
          font-size: 12px;
        }
        .pv-area {
          fill: url(#hybrid-ai-pv-fill);
        }
        .pv-line {
          fill: none;
          stroke: #f59e0b;
          stroke-width: 3.4;
          stroke-linejoin: round;
          stroke-linecap: round;
        }
        .load-line {
          fill: none;
          stroke: #0f766e;
          stroke-width: 3.4;
          stroke-linejoin: round;
          stroke-linecap: round;
        }
        .legend {
          display: flex;
          gap: 12px;
          align-items: center;
          flex-wrap: wrap;
        }
        .legend-item {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 0.82rem;
          color: rgba(15, 23, 42, 0.74);
        }
        .legend-swatch {
          width: 12px;
          height: 12px;
          border-radius: 999px;
          display: inline-block;
        }
        .legend-swatch.pv { background: #f59e0b; }
        .legend-swatch.load { background: #0f766e; }
        .fact-card,
        .slot-card,
        .action-row,
        .hour-row,
        .notice-item,
        .empty-state {
          padding: 12px;
        }
        .fact-value,
        .action-name,
        .hour-mode {
          margin-top: 6px;
          font-size: 0.94rem;
          font-weight: 600;
          color: var(--hybrid-ink);
          line-height: 1.5;
          word-break: break-word;
        }
        .slot-card {
          background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.92));
          color: white;
        }
        .slot-program,
        .slot-label,
        .hour-time,
        .hour-flow,
        .muted,
        .empty-copy,
        .action-reason {
          color: rgba(15, 23, 42, 0.78);
          line-height: 1.5;
        }
        .slot-card .slot-program,
        .slot-card .slot-label {
          color: rgba(255, 255, 255, 0.82);
        }
        .slot-hours {
          margin-top: 10px;
          font-size: 1.16rem;
          font-weight: 700;
        }
        .slot-mode { color: #fde68a; }
        .action-state {
          padding: 6px 10px;
          border-radius: 999px;
          background: rgba(15, 118, 110, 0.12);
          color: #115e59;
          font-size: 0.8rem;
          font-weight: 700;
          align-self: flex-start;
        }
        .hour-row {
          display: grid;
          grid-template-columns: 110px minmax(0, 1fr) auto auto;
          gap: 10px;
          align-items: center;
        }
        .empty-title {
          font-size: 1rem;
          font-weight: 700;
          color: var(--hybrid-ink);
        }
        @media (max-width: 900px) {
          .hero,
          .grid-panels { grid-template-columns: 1fr; }
        }
        @media (max-width: 620px) {
          .hero-stats,
          .fact-grid,
          .slot-grid,
          .action-buttons,
          .grid-panels { grid-template-columns: 1fr; }
          .hour-row { grid-template-columns: 1fr; }
        }
      </style>
    `;
  }
}

class HybridAiCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...DEFAULT_CONFIG, ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    const entityOptions = Object.keys(this._hass?.states || {})
      .filter((entityId) => entityId.startsWith("sensor.") && entityId.endsWith("_plan_summary"))
      .map((entityId) => `<option value="${entityId}"></option>`)
      .join("");

    this.innerHTML = `
      <div style="display:grid;gap:12px;padding:8px 0;">
        <label>
          <div>Tytul</div>
          <input id="title" type="text" value="${this._config?.title || ""}" style="width:100%;" />
        </label>
        <label>
          <div>Glowna encja</div>
          <input id="entity" list="hybrid-ai-entities" type="text" value="${this._config?.entity || ""}" style="width:100%;" />
          <datalist id="hybrid-ai-entities">${entityOptions}</datalist>
        </label>
        ${this._checkbox("show_settings", "Pokaz ustawienia planera")}
        ${this._checkbox("show_discovery", "Pokaz status autowykrywania")}
        ${this._checkbox("show_tou_plan", "Pokaz okna TOU")}
        ${this._checkbox("show_actions", "Pokaz zaplanowane akcje")}
        ${this._checkbox("show_hourly_schedule", "Pokaz plan godzinowy")}
        ${this._checkbox("show_price_context", "Pokaz kontekst cenowy")}
        ${this._checkbox("show_chart", "Pokaz wykres PV i zuzycia")}
        ${this._checkbox("compact", "Tryb kompaktowy")}
      </div>
    `;

    this.querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", () => this._valueChanged());
    });
  }

  _checkbox(key, label) {
    const checked = this._config?.[key] ? "checked" : "";
    return `
      <label style="display:flex;gap:8px;align-items:center;">
        <input id="${key}" type="checkbox" ${checked} />
        <span>${label}</span>
      </label>
    `;
  }

  _valueChanged() {
    const config = {
      ...this._config,
      title: this.querySelector("#title")?.value || "Hybrid AI",
      entity: this.querySelector("#entity")?.value || undefined,
      show_settings: this.querySelector("#show_settings")?.checked ?? true,
      show_discovery: this.querySelector("#show_discovery")?.checked ?? true,
      show_tou_plan: this.querySelector("#show_tou_plan")?.checked ?? true,
      show_actions: this.querySelector("#show_actions")?.checked ?? true,
      show_hourly_schedule: this.querySelector("#show_hourly_schedule")?.checked ?? true,
      show_price_context: this.querySelector("#show_price_context")?.checked ?? true,
      show_chart: this.querySelector("#show_chart")?.checked ?? true,
      compact: this.querySelector("#compact")?.checked ?? false,
    };

    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config },
        bubbles: true,
        composed: true,
      }),
    );
  }
}

if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, HybridAiCard);
}

if (!customElements.get("hybrid-ai-card-editor")) {
  customElements.define("hybrid-ai-card-editor", HybridAiCardEditor);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: CARD_TYPE,
  name: "Hybrid AI Card",
  description: "Dashboard card for Hybrid AI Energy Manager with PV, load, TOU and discovery diagnostics.",
  preview: true,
  documentationURL: "https://github.com/Lauferek2007/deyeai",
});
