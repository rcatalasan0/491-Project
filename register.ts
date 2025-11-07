const $ = (sel) => document.querySelector(sel);

const els = {
  form: $("#registerForm"),
  btn: $("#registerButton"),
  status: $("#status"),
};

function toast(kind, msg) {
  els.status.className = `toast ${kind} show`;
  els.status.textContent = msg;
}

function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

function validatePassword(password) {
  // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
  const minLength = password.length >= 8;
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  
  return minLength && hasUpper && hasLower && hasNumber;
}

els.form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = $("#email").value.trim();
  const password = $("#password").value;
  const confirmPassword = $("#confirmPassword").value;

  // Client-side validation
  if (!email) {
    toast("err", "Email address is required.");
    return;
  }

  if (!validateEmail(email)) {
    toast("err", "Please enter a valid email address.");
    return;
  }

  if (!password) {
    toast("err", "Password is required.");
    return;
  }

  if (!validatePassword(password)) {
    toast("err", "Password must be at least 8 characters with uppercase, lowercase, and a number.");
    return;
  }

  if (password !== confirmPassword) {
    toast("err", "Passwords do not match.");
    return;
  }

  // Disable form during submission
  els.btn.disabled = true;
  els.btn.textContent = "Registering...";
  toast("info", "Creating your account...");

  try {
    // Send registration request to backend API
    const response = await fetch("/api/register", {
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
      // Registration successful
      toast("ok", `✅ Registration Successful! Account created for ${email}. Redirecting to login...`);
      els.form.reset();
      
      // Redirect to login page after 2 seconds
      setTimeout(() => {
        window.location.href = "login.html";
      }, 2000);
      
    } else {
      // Handle error response from server
      const errorMsg = data.error || data.message || "Registration failed. Please try again.";
      toast("err", errorMsg);
      els.btn.disabled = false;
      els.btn.textContent = "Register";
    }
    
  } catch (error) {
    // Network or other errors
    console.error("Registration error:", error);
    toast("err", "Unable to connect to server. Please check your connection and try again.");
    els.btn.disabled = false;
    els.btn.textContent = "Register";
  }
});

toast("info", "Enter your details to create an account.");