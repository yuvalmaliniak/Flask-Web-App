document.getElementById('taskForm').addEventListener('submit', async function(e) {
  e.preventDefault(); // Stop the page from refreshing

  const title = document.getElementById('taskTitle').value;

  const res = await fetch('/api/tasks', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ title })
  });

  const data = await res.json();
  console.log('Task added:', data);
});
