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

els.form.addEventListener("submit", async (e) => {
  e.preventDefault(); // Stop the default form submission

  const email = $("#email").value.trim();
  const password = $("#password").value;

  console.log(`Attempting login for: ${email}`);
  els.btn.disabled = true;
  toast("info", "Authenticating...");

  try {
    // ⚡️ API CALL: Send login data to the Flask backend
    const response = await fetch("http://127.0.0.1:5000/api/login", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // Send email and password in the request body
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (response.status === 200) { // HTTP 200 OK
      // Login successful
      toast("ok", `Login successful! Redirecting to prediction tool...`);
      
      // Redirect to the main prediction page
      setTimeout(() => {
          window.location.href = 'prediction-tool.html';
      }, 1000);
      
    } else {
      // Login failed (e.g., 401 Unauthorized, 400 validation)
      const errorMsg = data.error || "Login failed.";
      toast("err", `Error: ${errorMsg}`);
    }
  } catch (error) {
    console.error("Network or API error:", error);
    toast("err", "A network error occurred. Check the server connection.");
  } finally {
    els.btn.disabled = false;
  }
});

toast("info", "Enter your email and password.");