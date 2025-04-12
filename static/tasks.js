const token = localStorage.getItem("token");
const taskList = document.getElementById("taskList");

document.getElementById("taskForm").onsubmit = async (e) => {
  e.preventDefault();
  const title = document.getElementById("title").value;
  const description = document.getElementById("description").value;

  const res = await fetch("/api/tasks", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ title, description })
  });

  if (res.ok) {
    document.getElementById("taskForm").reset();
    await fetch("/api/ai/recommend", {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` }
    });
    loadTasks();
  } else {
    alert("Failed to add task.");
  }
};

async function loadTasks() {
  taskList.innerHTML = "";

  const [taskRes, recRes] = await Promise.all([
    fetch("/api/tasks", { headers: { "Authorization": `Bearer ${token}` } }),
    fetch("/api/ai/recommend", {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` }
    })
  ]);

  const tasks = await taskRes.json();
  const recommendations = await recRes.json();

  tasks.forEach(task => {
    const rec = recommendations.find(r => r.task_id === task._id);
    const li = document.createElement("li");
    li.innerHTML = `
      <strong>${task.title}</strong>: ${task.description || ""}
      ${rec ? `
        <br><em>🧠 <b>AI Recommendation:</b> ${rec.recommendation}</em>
        <br>📂 <b>Category:</b> ${rec.category} | 
        ⏱️ <b>Estimated time in hours:</b> ${rec.estimated_time}
      ` : ""}
      <button onclick="deleteTask('${task._id}')">❌</button>
    `;
    taskList.appendChild(li);
  });
}

async function deleteTask(id) {
  const res = await fetch(`/api/tasks/${id}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (res.ok) loadTasks();
}

loadTasks();

document.getElementById("loadSchedule").onclick = async () => {
  const res = await fetch("/api/ai/schedule", {
    headers: { Authorization: `Bearer ${token}` }
  });
  const data = await res.json();
  document.getElementById("scheduleOutput").innerText = data.schedule || data.error;
};

document.getElementById("loadSummary").onclick = async () => {
  const res = await fetch("/api/ai/weekly_summary", {
    headers: { Authorization: `Bearer ${token}` }
  });
  const data = await res.json();
  document.getElementById("summaryOutput").innerText = data.summary || data.error;
};
