const $ = (sel) => document.querySelector(sel);

const els = {
  form: $("#loginForm"),
  btn: $("#loginButton"),
  status: $("#status"),
};

function toast(kind, msg) {
  // Use the toast logic from style.css
  els.status.className = `toast ${kind} show`;
  els.status.textContent = msg;
}

els.form.addEventListener("submit", (e) => {
  e.preventDefault(); // Stop the default form submission

  const email = $("#email").value.trim();
  const password = $("#password").value;

  // --- DEMO FUNCTIONALITY ---
  // In a real application, you'd send an API request here for verification.

  console.log(`Attempting login for: ${email}`);
  els.btn.disabled = true;

  // Simulate a network delay and authentication success
  setTimeout(() => {
    els.btn.disabled = false;
    
    // In a real app, this is where you'd check the server response.
    // For the demo, we assume success and redirect.
    toast("ok", `Login successful! Redirecting to prediction tool...`);
    
    // *** REDIRECT: Go to the main prediction page after successful login ***
    window.location.href = 'prediction-tool.html';
    
  }, 1500);
});

toast("info", "Enter your email and password.");