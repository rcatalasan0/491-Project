const $ = (sel) => document.querySelector(sel);

const els = {
  form: $("#loginForm"),
  btn: $("#loginButton"),
  status: $("#status"),
  emailInput: $("#email"),
  passwordInput: $("#password"),
};

function toast(kind, msg) {
  els.status.className = `toast ${kind} show`;
  els.status.textContent = msg;
}

els.form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = els.emailInput.value.trim();
  const password = els.passwordInput.value;

  if (!email || !password) {
    toast("err", "Please enter both email and password.");
    return;
  }

  console.log(`Attempting login for: ${email}`);
  
  // Disable form during submission
  els.btn.disabled = true;
  els.btn.textContent = "Logging in...";
  els.emailInput.disabled = true;
  els.passwordInput.disabled = true;
  
  toast("info", "Verifying credentials...");

  try {
    // Send login request to backend API
    const response = await fetch("http://127.0.0.1:5000/api/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      // Login successful
      toast("ok", `✅ Login successful! Welcome back, ${email}. Redirecting...`);
      
      // Store user session (you can enhance this with JWT tokens later)
      sessionStorage.setItem('user', JSON.stringify(data.user));
      sessionStorage.setItem('userEmail', email);
      sessionStorage.setItem('loginTime', new Date().toISOString());
      
      // Keep button disabled during redirect
      els.btn.textContent = "Redirecting...";
      
      // Redirect to prediction tool
      setTimeout(() => {
        window.location.href = 'prediction-tool.html';
      }, 1500);
      
    } else {
      // Handle error response
      const errorMsg = data.error || "Login failed. Please check your credentials.";
      toast("err", errorMsg);
      
      // Re-enable form
      els.btn.disabled = false;
      els.btn.textContent = "Log In";
      els.emailInput.disabled = false;
      els.passwordInput.disabled = false;
      
      // Clear password field on error
      els.passwordInput.value = "";
      els.passwordInput.focus();
    }
    
  } catch (error) {
    // Network or other errors
    console.error("Login error:", error);
    toast("err", "Unable to connect to server. Please make sure the Flask app is running.");
    
    // Re-enable form
    els.btn.disabled = false;
    els.btn.textContent = "Log In";
    els.emailInput.disabled = false;
    els.passwordInput.disabled = false;
  }
});

// Check if user just registered (coming from register page)
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('registered') === 'true') {
  toast("ok", "✅ Registration successful! Please log in with your new account.");
} else {
  toast("info", "Enter your email and password.");
}