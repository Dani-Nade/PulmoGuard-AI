document.addEventListener("DOMContentLoaded", () => {
    // panel toggle
    const signUpBtn = document.getElementById("signUp");
    const signInBtn = document.getElementById("signIn");
    const container = document.getElementById("container");
    signUpBtn.addEventListener("click", () => container.classList.add("right-panel-active"));
    signInBtn.addEventListener("click", () => container.classList.remove("right-panel-active"));
  
    // client-side signup validation
    const form = document.getElementById("signup-form");
    form.addEventListener("submit", e => {
      e.preventDefault();
      const name     = form.name.value.trim();
      const email    = form.email.value.trim();
      const password = form.password.value;
  
      if (!name) {
        showError("Name is required.");
        return;
      }
      const emailRe = /^[\w.-]+@[\w.-]+\.\w+$/;
      if (!emailRe.test(email)) {
        showError("Invalid email address.");
        return;
      }
      const pwdRe = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*\W).{8,}$/;
      if (!pwdRe.test(password)) {
        showError("Password must be ≥8 chars, include upper & lower case, a number & special char.");
        return;
      }
  
      // passes client‐side checks
      showSuccess("All checks passed! Submitting...");
      setTimeout(() => form.submit(), 800);
    });
  });
  