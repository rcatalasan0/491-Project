const $ = (sel) => document.querySelector(sel);

const els = {
  form: $("#registerForm"),
  btn: $("#registerButton"),
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
  const confirmPassword = $("#confirmPassword").value;

  if (password !== confirmPassword) {
    toast("err", "Error: Passwords do not match.");
    return;
  }

  // --- DEMO FUNCTIONALITY ---
  // In a real application, you'd send an API request here.
  // For this demo, we just show a success message.

  console.log(`Attempting registration for: ${email}`);
  els.btn.disabled = true;

  // Simulate a network delay
  setTimeout(() => {
    els.btn.disabled = false;
    toast("ok", `Success! User '${email}' registered (demo mode).`);
    els.form.reset();
  }, 1500);
});

toast("info", "Enter your details to register.");