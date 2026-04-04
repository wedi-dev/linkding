import { HeadlessElement } from "../utils/element.js";

class StartWidget extends HeadlessElement {
  init() {
    const header = this.querySelector(".widget-header");
    if (header) {
      header.addEventListener("click", () => {
        this.toggleAttribute("collapsed");
      });
    }
  }
}

customElements.define("ld-start-widget", StartWidget);
