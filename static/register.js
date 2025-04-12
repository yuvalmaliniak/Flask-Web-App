document.getElementById("registerForm").onsubmit = async (e) => {
  e.preventDefault();
  const res = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.getElementById("username").value,
      password: document.getElementById("password").value,
    }),
  });
  const data = await res.json();
  if (res.ok) {
    alert("Registered! You can now log in.");
    window.location.href = "/";
  } else {
    alert(data.error || data.message);
  }
};
