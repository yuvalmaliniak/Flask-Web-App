document.getElementById("loginForm").onsubmit = async (e) => {
  e.preventDefault();
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.getElementById("username").value,
      password: document.getElementById("password").value,
    }),
  });
  const data = await res.json();
  if (res.ok) {
    localStorage.setItem("token", data.token);
    window.location.href = "/tasks";
  } else {
    alert(data.message || "Login failed");
  }
};
