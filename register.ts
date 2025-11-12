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

els.form.addEventListener("submit", async (e) => {
  e.preventDefault(); // Stop the default form submission

  const email = $("#email").value.trim();
  const password = $("#password").value;
  const confirmPassword = $("#confirmPassword").value;

  if (password !== confirmPassword) {
    toast("err", "Error: Passwords do not match.");
    return;
  }

  els.btn.disabled = true;
  toast("info", "Registering account...");
  
  try {
    // ⚡️ API CALL: Send registration data to the Flask backend
    const response = await fetch("http://127.0.0.1:5000/api/register", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // Send email and password in the request body
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    
    if (response.status === 201) { // HTTP 201 Created
      // Registration successful
      toast("ok", `Success! Account created for ${email}. Redirecting to login...`);
      els.form.reset();
      
      // Redirect to the login page after successful registration
      setTimeout(() => {
        window.location.href = 'login.html';
      }, 1500);

    } else {
      // Registration failed (e.g., 400 validation, 409 conflict)
      const errorMsg = data.error || "Registration failed due to an unknown error.";
      toast("err", `Error: ${errorMsg}`);
    }

  } catch (error) {
    console.error("Network or API error:", error);
    toast("err", "A network error occurred. Check the server connection.");
  } finally {
    els.btn.disabled = false;
  }
});

toast("info", "Enter your details to register.");