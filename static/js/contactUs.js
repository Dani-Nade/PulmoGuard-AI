// static/js/contactUs.js

// Show / hide helpers
function showError(msg) {
  const container = document.getElementById("error-message");
  const textEl    = document.getElementById("error-text");
  textEl.innerText = msg;
  container.classList.add("show");
  setTimeout(() => container.classList.remove("show"), 5000);
}

function showSuccess(msg) {
  const container = document.getElementById("success-message");
  const textEl    = document.getElementById("success-text");
  textEl.innerText = msg;
  container.classList.add("show");
  setTimeout(() => container.classList.remove("show"), 5000);
}

function closeError() {
  document.getElementById("error-message").classList.remove("show");
}

function closeSuccess() {
  document.getElementById("success-message").classList.remove("show");
}

// Main
document.addEventListener("DOMContentLoaded", () => {
  // Make sure the containers exist
  if (!document.getElementById("error-message") ||
      !document.getElementById("success-message")) {
    console.error("Error/success containers not found in DOM");
    return;
  }

  const form = document.querySelector(".container.contact-form form");
  if (!form) {
    console.error("Contact form not found in DOM");
    return;
  }

  form.addEventListener("submit", async e => {
    e.preventDefault();

    // Gather values
    const name    = form.txtName.value.trim();
    const email   = form.txtEmail.value.trim();
    const phone   = form.txtPhone.value.trim();
    const message = form.txtMsg.value.trim();

    // Simple front-end validation
    if (!name || !email || !phone || !message) {
      return showError("All fields are required.");
    }

    try {
      const response = await fetch("/send-contact-form", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, phone, message }),
      });

      let payload;
      try {
        payload = await response.json();
      } catch (_) {
        // Non-JSON or empty response
        throw new Error("Invalid response from server.");
      }

      if (response.ok) {
        showSuccess(payload.message || "Your message has been sent successfully!");
        form.reset();
      } else {
        showError(payload.error || "Failed to send message. Please try again.");
      }
    } catch (err) {
      console.error("Contact form submission error:", err);
      showError("Network error. Please try again later.");
    }
  });
});
