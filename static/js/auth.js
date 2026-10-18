document.getElementById("authForm").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.getElementById("authMessage");
  const setupRequired = document.body.dataset.setupRequired === "true";
  const submitButton = form.querySelector("button[type='submit']");
  const payload = Object.fromEntries(new FormData(form));
  submitButton.disabled = true;
  submitButton.textContent = setupRequired ? "Creating account..." : "Signing in...";
  message.className = "validation-alert";
  message.style.display = "none";

  try {
    const response = await fetch(setupRequired ? "/api/auth/setup" : "/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok || !result.success) throw new Error(result.error || "Authentication failed.");
    window.location.assign("/");
  } catch (error) {
    message.className = "validation-alert error";
    message.style.display = "block";
    message.textContent = error.message;
    submitButton.disabled = false;
    submitButton.textContent = setupRequired ? "Create admin account" : "Sign in";
  }
});
