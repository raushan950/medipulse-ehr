const panels = [...document.querySelectorAll("[data-panel]")];
const message = document.getElementById("authMessage");

function showPanel(name) {
  panels.forEach(panel => { panel.hidden = panel.dataset.panel !== name; });
  message.style.display = "none";
}

document.querySelectorAll("[data-show-panel]").forEach(button => {
  button.addEventListener("click", () => showPanel(button.dataset.showPanel));
});

const resetToken = new URLSearchParams(window.location.search).get("token");
if (resetToken) {
  document.getElementById("resetToken").value = resetToken;
  window.history.replaceState({}, "", "/auth");
  showPanel("reset");
}

document.querySelectorAll(".auth-form").forEach(form => {
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const submitButton = form.querySelector("button[type='submit']");
    const originalText = submitButton.textContent;
    const payload = Object.fromEntries(new FormData(form));
    submitButton.disabled = true;
    submitButton.textContent = "Please wait...";
    message.className = "validation-alert";
    message.style.display = "none";

    try {
      const response = await fetch(form.dataset.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error(result.error || "Request failed.");

      if (form.dataset.redirect === "true") {
        window.location.assign("/");
        return;
      }
      message.textContent = result.message;
      if (result.dev_reset_url) {
        const resetLink = document.createElement("a");
        resetLink.href = result.dev_reset_url;
        resetLink.textContent = " Open reset link";
        resetLink.rel = "noreferrer";
        message.append(resetLink);
      }
      message.style.display = "block";
      if (form.dataset.resetComplete === "true") {
        window.history.replaceState({}, "", "/auth");
        showPanel("login");
        message.textContent = result.message;
        message.style.display = "block";
      }
    } catch (error) {
      message.className = "validation-alert error";
      message.style.display = "block";
      message.textContent = error.message;
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = originalText;
    }
  });
});
