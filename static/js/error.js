// Show an error message
function showError(message) {
    const box = document.getElementById("error-message");
    document.getElementById("error-text").innerText = message;
    box.classList.add("show");
    setTimeout(() => box.classList.remove("show"), 5000);
  }
  function closeError() {
    document.getElementById("error-message").classList.remove("show");
  }
  
  // Show a success message
  function showSuccess(message) {
    const box = document.getElementById("success-message");
    document.getElementById("success-text").innerText = message;
    box.classList.add("show");
    setTimeout(() => box.classList.remove("show"), 5000);
  }
  function closeSuccess() {
    document.getElementById("success-message").classList.remove("show");
  }
  