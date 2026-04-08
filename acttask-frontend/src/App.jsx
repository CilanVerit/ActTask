import { useState, useEffect } from "react";
import Login from "./Login";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem("token")
  );

  const [tasks, setTasks] = useState(null);
  const [newTask, setNewTask] = useState("");

  useEffect(() => {
    if (isLoggedIn) {
      fetchTasks();
    }
  }, [isLoggedIn]);

  const fetchTasks = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await fetch("http://127.0.0.1:5000/tasks", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.status === 401) {
        localStorage.removeItem("token");
        setIsLoggedIn(false);
        return;
      }

      const data = await res.json();

      setTasks(data.task); // or data.tasks if needed
    } catch (err) {
      console.error(err);

      // Backend down → force logout
      localStorage.removeItem("token");
      setIsLoggedIn(false);
    }
  };

  const handleAddTask = async () => {
    if (!newTask.trim()) return;

    try {
      const token = localStorage.getItem("token");

      const res = await fetch("http://127.0.0.1:5000/tasks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: newTask,
        }),
      });

      if (res.status === 401) {
        localStorage.removeItem("token");
        setIsLoggedIn(false);
        return;
      }

      const data = await res.json();

      fetchTasks();

      setNewTask("");
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleTask = async (id, currentStatus) => {
    try {
      const token = localStorage.getItem("token");

      const res = await fetch(`http://127.0.0.1:5000/tasks/${id}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: currentStatus === "Completed" ? "Pending" : "Completed",
        }),
      });

      if (res.status === 401) {
        localStorage.removeItem("token");
        setIsLoggedIn(false);
        return;
      }

      fetchTasks();
    } catch (err) {
      console.error(err);
    }
  };

  if (!isLoggedIn) {
    return <Login onLogin={() => setIsLoggedIn(true)} />;
  }

  return (
    <div className="p-6">
      <button
        onClick={() => {
          localStorage.removeItem("token");
          setIsLoggedIn(false);
        }}
        className="mb-4 bg-red-500 text-white px-3 py-1 rounded"
      >
        Logout
      </button>

    <div className="mb-4 flex gap-2">
      <input
        type="text"
        value={newTask}
        onChange={(e) => setNewTask(e.target.value)}
        placeholder="Enter new task..."
        className="border p-2 rounded w-full"
      />

      <button
        onClick={handleAddTask}
        className="bg-blue-500 text-white px-4 rounded whitespace-nowrap"
      >
        Add New Task
      </button>
    </div>

      <h1 className="text-2xl font-bold mb-4">Your Tasks</h1>

      {tasks === null ? (
        <p>Loading...</p>
      ) : tasks.length === 0 ? (
        <p>No tasks found</p>
      ) : (
        <ul className="space-y-2">
          {tasks.map((task) => (
            <li
              key={task.id}
              className="bg-white p-3 rounded shadow flex justify-between items-center"
            >
              <div>
                <p className="font-semibold">{task.title}</p>
                <p className="text-sm text-gray-500">
                  Status: {task.status}
                </p>
              </div>

              <button
                onClick={() => handleToggleTask(task.id, task.status)}
                className="bg-green-500 text-white px-3 py-1 rounded"
              >
                Mark Complete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}