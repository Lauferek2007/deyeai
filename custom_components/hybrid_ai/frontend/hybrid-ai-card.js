const CARD_TYPE = "hybrid-ai-card";
const DEFAULT_CONFIG = {
  title: "Hybrid AI",
  show_settings: true,
  show_tou_plan: true,
  show_actions: true,
  show_hourly_schedule: true,
  show_price_context: true,
  compact: false,
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
    return this._config.compact ? 6 : 10;
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
      return Array.isArray(state?.attributes?.adapter_actions);
    });

    if (preferred) {
      return preferred;
    }

    return Object.keys(this._hass.states).find((entityId) => {
      const state = this._hass.states[entityId];
      return (
        entityId.startsWith("sensor.") &&
        Array.isArray(state?.attributes?.adapter_actions) &&
        Array.isArray(state?.attributes?.tou_plan)
      );
    });
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
          <div class="content">
            <div class="empty">
              No Hybrid AI entity found. Set the entity manually or add the integration first.
            </div>
          </div>
        </ha-card>
      `;
      return;
    }

    const attrs = stateObj.attributes || {};
    const hourly = attrs.hourly_schedule || [];
    const touPlan = attrs.tou_plan || [];
    const actions = attrs.adapter_actions || [];
    const prices = attrs.price_context || {};
    const settings = attrs.settings || {};
    const activeMode = hourly[0]?.mode || "unknown";
    const nextTou = touPlan[0]
      ? `P${touPlan[0].program}: ${touPlan[0].label} ${this._hour(touPlan[0].start_hour)}-${this._hour(touPlan[0].end_hour)}`
      : "none";

    this.shadowRoot.innerHTML = `
      <ha-card header="${this._config.title}">
        ${this._style()}
        <div class="content ${this._config.compact ? "compact" : ""}">
          <div class="summary">${stateObj.state || "No plan"}</div>
          <div class="topline">
            <span class="chip">Adapter: ${attrs.adapter || "unknown"}</span>
            <span class="chip ${attrs.dry_run ? "warn" : "ok"}">${attrs.dry_run ? "DRY RUN" : "WRITE MODE"}</span>
            <span class="chip">Active: ${activeMode}</span>
            <span class="chip">Next TOU: ${nextTou}</span>
          </div>

          <div class="metrics">
            ${this._metric("PV 24h", this._formatNumber(attrs.forecast_solar_kwh, "kWh"))}
            ${this._metric("Load 24h", this._formatNumber(attrs.forecast_load_kwh, "kWh"))}
            ${this._metric("Surplus", this._formatNumber(attrs.expected_surplus_kwh, "kWh"))}
            ${this._metric("Morning SOC", this._formatNumber(attrs.target_morning_soc, "%"))}
            ${this._metric("Confidence", this._formatPercent(attrs.forecast_confidence))}
          </div>

          <div class="actions-row">
            <button id="refresh-btn" class="primary">Run plan</button>
            <button id="discover-btn" class="secondary">Autodiscovery</button>
          </div>

          ${this._config.show_settings ? this._renderSettings(settings) : ""}
          ${this._config.show_price_context ? this._renderPrices(prices) : ""}
          ${this._config.show_tou_plan ? this._renderTou(touPlan) : ""}
          ${this._config.show_actions ? this._renderActions(actions) : ""}
          ${this._config.show_hourly_schedule ? this._renderHourly(hourly) : ""}
        </div>
      </ha-card>
    `;

    const refreshButton = this.shadowRoot.getElementById("refresh-btn");
    if (refreshButton) {
      refreshButton.onclick = () => this._hass.callService("hybrid_ai", "run_optimization", {});
    }

    const discoverButton = this.shadowRoot.getElementById("discover-btn");
    if (discoverButton) {
      discoverButton.onclick = () => this._hass.callService("hybrid_ai", "discover_entities", {});
    }
  }

  _renderSettings(settings) {
    return `
      <div class="section">
        <div class="section-title">Active settings</div>
        <div class="list-grid">
          <div>Auto discovery: <strong>${settings.auto_discovery ? "on" : "off"}</strong></div>
          <div>Write mode: <strong>${settings.enable_write_mode ? "on" : "off"}</strong></div>
          <div>Min SOC: <strong>${this._formatNumber(settings.min_soc, "%")}</strong></div>
          <div>Max SOC: <strong>${this._formatNumber(settings.max_soc, "%")}</strong></div>
          <div>Export: <strong>${settings.export_allowed ? "on" : "off"}</strong></div>
          <div>Grid charge: <strong>${settings.grid_charge_allowed ? "on" : "off"}</strong></div>
          <div>Cycle cost: <strong>${this._formatNumber(settings.battery_cycle_cost, "")}</strong></div>
          <div>Update interval: <strong>${this._formatNumber(settings.update_interval_minutes, "min")}</strong></div>
        </div>
      </div>
    `;
  }

  _renderPrices(prices) {
    return `
      <div class="section">
        <div class="section-title">Price context</div>
        <div class="list-grid">
          <div>Avg import: <strong>${this._formatNumber(prices.avg_import_price, "")}</strong></div>
          <div>Avg export: <strong>${this._formatNumber(prices.avg_export_price, "")}</strong></div>
          <div>Cheapest import: <strong>${this._formatNumber(prices.cheapest_import_price, "")}</strong></div>
          <div>Best export: <strong>${this._formatNumber(prices.highest_export_price, "")}</strong></div>
        </div>
      </div>
    `;
  }

  _renderTou(items) {
    const rows = items.length
      ? items
          .map(
            (item) => `
              <div class="list-row">
                <span>P${item.program}</span>
                <strong>${item.label}</strong>
                <span>${this._hour(item.start_hour)}-${this._hour(item.end_hour)}</span>
              </div>
            `,
          )
          .join("")
      : `<div class="muted">No active TOU slots.</div>`;

    return `
      <div class="section">
        <div class="section-title">TOU slots</div>
        ${rows}
      </div>
    `;
  }

  _renderActions(items) {
    const rows = items.length
      ? items
          .map(
            (item) => `
              <div class="list-row">
                <span>${item.action}</span>
                <strong>${item.value ?? ""}</strong>
                <span>${item.executed ? "done" : item.dry_run ? "dry-run" : "queued"}</span>
              </div>
            `,
          )
          .join("")
      : `<div class="muted">No adapter actions.</div>`;

    return `
      <div class="section">
        <div class="section-title">Adapter actions</div>
        ${rows}
      </div>
    `;
  }

  _renderHourly(items) {
    const preview = items.slice(0, this._config.compact ? 6 : 12);
    const rows = preview.length
      ? preview
          .map(
            (item) => `
              <div class="list-row wide">
                <span>${this._formatDate(item.start)}</span>
                <strong>${item.mode}</strong>
                <span>load ${this._formatNumber(item.expected_load_kwh, "kWh")}</span>
                <span>pv ${this._formatNumber(item.expected_pv_kwh, "kWh")}</span>
              </div>
            `,
          )
          .join("")
      : `<div class="muted">No hourly plan.</div>`;

    return `
      <div class="section">
        <div class="section-title">Hourly plan</div>
        ${rows}
      </div>
    `;
  }

  _metric(label, value) {
    return `
      <div class="metric">
        <div class="metric-label">${label}</div>
        <div class="metric-value">${value}</div>
      </div>
    `;
  }

  _formatNumber(value, suffix) {
    if (value === undefined || value === null || value === "") {
      return "n/a";
    }
    const normalized = Number(value);
    if (Number.isNaN(normalized)) {
      return `${value}${suffix ? ` ${suffix}` : ""}`;
    }
    return `${normalized.toFixed(2)}${suffix ? ` ${suffix}` : ""}`;
  }

  _formatPercent(value) {
    if (value === undefined || value === null || value === "") {
      return "n/a";
    }
    return `${(Number(value) * 100).toFixed(0)} %`;
  }

  _hour(value) {
    return `${String(Number(value)).padStart(2, "0")}:00`;
  }

  _formatDate(value) {
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
        .content {
          padding: 16px;
          display: grid;
          gap: 16px;
        }
        .content.compact {
          gap: 12px;
        }
        .summary {
          font-size: 1.05rem;
          line-height: 1.5;
          padding: 12px 14px;
          border-radius: 14px;
          background: linear-gradient(135deg, rgba(51, 102, 204, 0.12), rgba(16, 185, 129, 0.10));
        }
        .topline {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .chip {
          padding: 6px 10px;
          border-radius: 999px;
          background: var(--secondary-background-color);
          font-size: 0.85rem;
        }
        .chip.warn {
          background: rgba(245, 158, 11, 0.18);
        }
        .chip.ok {
          background: rgba(16, 185, 129, 0.18);
        }
        .metrics {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 10px;
        }
        .metric {
          padding: 12px;
          border-radius: 14px;
          background: var(--ha-card-background, var(--card-background-color));
          border: 1px solid var(--divider-color);
        }
        .metric-label {
          font-size: 0.82rem;
          opacity: 0.72;
        }
        .metric-value {
          margin-top: 6px;
          font-size: 1.15rem;
          font-weight: 600;
        }
        .actions-row {
          display: flex;
          gap: 10px;
          justify-content: flex-end;
        }
        button.primary,
        button.secondary {
          border-radius: 12px;
          padding: 10px 14px;
          cursor: pointer;
          font: inherit;
        }
        button.primary {
          border: 0;
          color: white;
          background: linear-gradient(135deg, #1d4ed8, #0f766e);
        }
        button.secondary {
          border: 1px solid var(--divider-color);
          color: var(--primary-text-color);
          background: var(--secondary-background-color);
        }
        .section {
          display: grid;
          gap: 8px;
        }
        .section-title {
          font-size: 0.95rem;
          font-weight: 600;
        }
        .list-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 8px;
        }
        .list-row {
          display: grid;
          grid-template-columns: 56px 1fr auto;
          gap: 8px;
          align-items: center;
          padding: 8px 10px;
          border-radius: 12px;
          background: var(--secondary-background-color);
        }
        .list-row.wide {
          grid-template-columns: 110px 1fr auto auto;
        }
        .muted,
        .empty {
          opacity: 0.72;
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
      .filter((entityId) => {
        if (!entityId.startsWith("sensor.")) {
          return false;
        }
        const attrs = this._hass.states[entityId]?.attributes || {};
        return Array.isArray(attrs.adapter_actions);
      })
      .map((entityId) => `<option value="${entityId}"></option>`)
      .join("");

    this.innerHTML = `
      <div style="display:grid;gap:12px;padding:8px 0;">
        <label>
          <div>Title</div>
          <input id="title" type="text" value="${this._config?.title || ""}" style="width:100%;" />
        </label>
        <label>
          <div>Main entity</div>
          <input id="entity" list="hybrid-ai-entities" type="text" value="${this._config?.entity || ""}" style="width:100%;" />
          <datalist id="hybrid-ai-entities">${entityOptions}</datalist>
        </label>
        ${this._checkbox("show_settings", "Show active settings")}
        ${this._checkbox("show_tou_plan", "Show TOU slots")}
        ${this._checkbox("show_actions", "Show adapter actions")}
        ${this._checkbox("show_hourly_schedule", "Show hourly plan")}
        ${this._checkbox("show_price_context", "Show price context")}
        ${this._checkbox("compact", "Compact mode")}
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
      show_tou_plan: this.querySelector("#show_tou_plan")?.checked ?? true,
      show_actions: this.querySelector("#show_actions")?.checked ?? true,
      show_hourly_schedule: this.querySelector("#show_hourly_schedule")?.checked ?? true,
      show_price_context: this.querySelector("#show_price_context")?.checked ?? true,
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
  description: "Universal dashboard card for Hybrid AI Energy Manager.",
  preview: true,
  documentationURL: "https://github.com/Lauferek2007/deyeai",
});
