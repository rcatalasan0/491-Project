const $ = (sel) => document.querySelector(sel);

const els = {
  form: $("#registerForm"),
  btn: $("#registerButton"),
  status: $("#status"),
  emailInput: $("#email"),
  passwordInput: $("#password"),
  confirmPasswordInput: $("#confirmPassword"),
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
  
  return {
    valid: minLength && hasUpper && hasLower && hasNumber,
    minLength,
    hasUpper,
    hasLower,
    hasNumber
  };
}

function getPasswordStrength(password) {
  const validation = validatePassword(password);
  let strength = 0;
  
  if (validation.minLength) strength++;
  if (validation.hasUpper) strength++;
  if (validation.hasLower) strength++;
  if (validation.hasNumber) strength++;
  
  if (strength <= 1) return { level: 'weak', color: '#ef4444' };
  if (strength <= 2) return { level: 'fair', color: '#f59e0b' };
  if (strength <= 3) return { level: 'good', color: '#10b981' };
  return { level: 'strong', color: '#16a34a' };
}

// Real-time password validation feedback
if (els.passwordInput) {
  els.passwordInput.addEventListener('input', (e) => {
    const password = e.target.value;
    if (password.length > 0) {
      const strength = getPasswordStrength(password);
      const validation = validatePassword(password);
      
      let feedback = `Password strength: ${strength.level}`;
      if (!validation.valid) {
        feedback += ' - Need: ';
        const missing = [];
        if (!validation.minLength) missing.push('8+ chars');
        if (!validation.hasUpper) missing.push('uppercase');
        if (!validation.hasLower) missing.push('lowercase');
        if (!validation.hasNumber) missing.push('number');
        feedback += missing.join(', ');
      }
      
      toast('info', feedback);
    }
  });
}

els.form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = els.emailInput.value.trim();
  const password = els.passwordInput.value;
  const confirmPassword = els.confirmPasswordInput.value;

  // Client-side validation
  if (!email) {
    toast("err", "Email address is required.");
    els.emailInput.focus();
    return;
  }

  if (!validateEmail(email)) {
    toast("err", "Please enter a valid email address.");
    els.emailInput.focus();
    return;
  }

  if (!password) {
    toast("err", "Password is required.");
    els.passwordInput.focus();
    return;
  }

  const passwordValidation = validatePassword(password);
  if (!passwordValidation.valid) {
    toast("err", "Password must be at least 8 characters with uppercase, lowercase, and a number.");
    els.passwordInput.focus();
    return;
  }

  if (password !== confirmPassword) {
    toast("err", "Passwords do not match.");
    els.confirmPasswordInput.focus();
    return;
  }

  // Disable form during submission
  els.btn.disabled = true;
  els.btn.textContent = "Creating Account...";
  els.emailInput.disabled = true;
  els.passwordInput.disabled = true;
  els.confirmPasswordInput.disabled = true;
  
  toast("info", "Creating your account...");

  try {
    // Send registration request to backend API
    const response = await fetch("http://127.0.0.1:5000/api/register", {
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
      toast("ok", `✅ Success! Account created for ${email}. Redirecting to login...`);
      
      // Clear form
      els.form.reset();
      
      // Keep button disabled during redirect
      els.btn.textContent = "Redirecting...";
      
      // Redirect to login page after 2 seconds
      setTimeout(() => {
        window.location.href = "login.html";
      }, 2000);
      
    } else {
      // Handle error response from server
      const errorMsg = data.error || data.message || "Registration failed. Please try again.";
      toast("err", errorMsg);
      
      // Re-enable form
      els.btn.disabled = false;
      els.btn.textContent = "Register";
      els.emailInput.disabled = false;
      els.passwordInput.disabled = false;
      els.confirmPasswordInput.disabled = false;
      
      // Focus on email if it's a duplicate account error
      if (errorMsg.includes("already exists")) {
        els.emailInput.focus();
        els.emailInput.select();
      }
    }
    
  } catch (error) {
    // Network or other errors
    console.error("Registration error:", error);
    toast("err", "Unable to connect to server. Please make sure the Flask app is running.");
    
    // Re-enable form
    els.btn.disabled = false;
    els.btn.textContent = "Register";
    els.emailInput.disabled = false;
    els.passwordInput.disabled = false;
    els.confirmPasswordInput.disabled = false;
  }
});

// Initial message
toast("info", "Enter your details to create an account.");