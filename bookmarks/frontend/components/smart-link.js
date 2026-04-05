import { HeadlessElement } from "../utils/element.js";

class SmartLinkOpen extends HeadlessElement {
  init() {
    // Find the parent modal
    const modal = this.closest(".modal");

    // Auto-focus and select when modal becomes active
    if (modal) {
      const observer = new MutationObserver(() => {
        if (modal.classList.contains("active")) {
          const firstInput = this.querySelector(".smart-link-param-input");
          if (firstInput) {
            firstInput.focus();
            firstInput.select();
          }
        }
      });
      observer.observe(modal, { attributes: true, attributeFilter: ["class"] });
    }

    // Chip click fills the corresponding input
    this.querySelectorAll(".smart-link-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const paramName = chip.dataset.param;
        const input = this.querySelector(
          `.smart-link-param-input[data-param="${paramName}"]`,
        );
        if (input) {
          input.value = chip.textContent.trim();
          input.focus();
        }
      });
    });
  }
}

customElements.define("ld-smart-link-open", SmartLinkOpen);
