import { HeadlessElement } from "../utils/element.js";

class WidgetForm extends HeadlessElement {
  init() {
    const typeSelect = this.querySelector("[name='widget_type']");
    if (!typeSelect) return;

    this._updateVisibility(typeSelect.value);
    typeSelect.addEventListener("change", () => {
      this._updateVisibility(typeSelect.value);
    });
  }

  _updateVisibility(type) {
    const fieldTypes = {
      bundle: this.querySelectorAll(".widget-field-bundle"),
      tag: this.querySelectorAll(".widget-field-tag"),
      filter: this.querySelectorAll(".widget-field-filter"),
    };

    for (const [fieldType, elements] of Object.entries(fieldTypes)) {
      elements.forEach((el) => {
        el.style.display = type === fieldType ? "" : "none";
      });
    }
  }
}

customElements.define("ld-widget-form", WidgetForm);
