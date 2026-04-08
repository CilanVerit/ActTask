import ReactMarkdown from "react-markdown";
import { useState, useEffect } from "react";
import Login from "./Login";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem("token")
  );

  const [tasks, setTasks] = useState(null);
  const [newTask, setNewTask] = useState("");
  const [view, setView] = useState("dashboard");  // "Dashboard" | "Tasks" | "AI" Tab view
  const [stats, setStats] = useState(null);
  const [aiPlan, setAIPlan] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const [aiFinal, setAIFinal] = useState(null);

  useEffect(() => {
    if (isLoggedIn) {
      fetchTasks();
      fetchStats();
    }
  }, [isLoggedIn]);

  const generatePlan = async () => {
    try {
      setLoadingAI(true);

      const token = localStorage.getItem("token");

      const res = await fetch("http://127.0.0.1:5000/ai/plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();

      setAIPlan(data.final_plan);
      setAIFinal({
        score: data.score,
        latency: data.latency,
      });

      setView("ai");

    } catch (err) {
      console.error(err);
    } finally {
      setLoadingAI(false);
    }
  };
  
  const fetchStats = async () => {
    const token = localStorage.getItem("token");

    const res = await fetch("http://127.0.0.1:5000/tasks/stats", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await res.json();
    setStats(data);
  };
  
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

  const formatDate = (dateString) => {
    if (!dateString) return "No deadline";
    return new Date(dateString).toLocaleString();
  };

  const getDeadlineColor = (dateString) => {
    if (!dateString) return "text-gray-400";

    const now = new Date();
    const deadline = new Date(dateString);

    const diffHours = (deadline - now) / (1000 * 60 * 60);

    if (deadline < now) return "text-red-500";      // overdue
    if (diffHours <= 24) return "text-yellow-500";  // due soon (within 24h)
    return "text-gray-400";                         // normal
  };

  const getStatusColor = (status) => {
    if (status === "Completed") return "text-green-500";
    if (status === "Overdue") return "text-red-500";
    return "text-yellow-500"; // Pending
  };

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
      <button
        onClick={() => setView("dashboard")}
        className="bg-gray-500 text-white px-4 py-2 rounded"
      >
        Dashboard
      </button>

      <button
        onClick={() => setView("tasks")}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        View Tasks
      </button>

      <button
        onClick={() => setView("ai")}
        className="bg-purple-500 text-white px-4 py-2 rounded"
      >
        AI Plan
      </button>
    </div>

  {view === "dashboard" && (
    <div className="max-w-4xl mx-auto">
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white p-4 rounded shadow">
          <p>Total</p>
          <h2 className="text-xl font-bold">{stats?.total ?? "-"}</h2>
        </div>

        <div className="bg-green-100 p-4 rounded shadow">
          <p>Completed</p>
          <h2 className="text-xl font-bold">{stats?.completed ?? "-"}</h2>
        </div>

        <div className="bg-yellow-100 p-4 rounded shadow">
          <p>Pending</p>
          <h2 className="text-xl font-bold">{stats?.pending ?? "-"}</h2>
        </div>

        <div className="bg-red-100 p-4 rounded shadow">
          <p>Overdue</p>
          <h2 className="text-xl font-bold">{stats?.overdue ?? "-"}</h2>
        </div>
      </div>

      <div className="flex justify-center mt-6">
        <button
          onClick={generatePlan}
          className="bg-purple-500 text-white px-6 py-3 rounded shadow"
        >
          {loadingAI ? "Generating AI Plan..." : "Generate AI Plan"}
        </button>
      </div>
    </div>
  )}
  
  {view === "tasks" && (
  <div>
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

              <p className={`text-sm ${getStatusColor(task.status)}`}>
                Status: {task.status}
              </p>

              <p className={`text-sm ${getDeadlineColor(task.deadline)}`}>
                Deadline: {formatDate(task.deadline)}
              </p>
            </div>

            <button
              onClick={() => handleToggleTask(task.id, task.status)}
              className="bg-green-500 text-white px-3 py-1 rounded"
            >
              {task.status === "Completed"
                ? "Mark Pending"
                : "Mark Complete"}
            </button>
          </li>
        ))}
      </ul>
    )}
  </div>
  )}
  {view === "ai" && (
    <div className="max-w-2xl mx-auto">
      <div className="relative h-12 mb-4">
        <button
          onClick={() => setView("dashboard")}
          className="absolute left-0 top-1/2 -translate-y-1/2 bg-gray-500 text-white px-3 py-1 rounded"
        >
          ← Back to Dashboard
        </button>

        <h2 className="text-xl font-bold text-center">Your AI Plan</h2>
      </div>

      {aiFinal && (
        <div className="flex justify-between items-center mb-4 text-sm text-gray-600">
          <span>
            Score: <span className="font-semibold">{aiFinal.score}/10</span> • Latency: {aiFinal.latency}s
          </span>
        </div>
      )}

      <div className="mt-16">
        {aiPlan ? (
          <div className="bg-white p-6 rounded-xl shadow-lg prose">
            <ReactMarkdown>{aiPlan}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-center text-gray-400 italic mt-10">
            No AI plan yet. Click "Generate AI Plan" to start.
          </p>
        )}
      </div>
      <div className="flex justify-center mt-8">
        <button
          onClick={generatePlan}
          disabled={loadingAI}
          className={`px-6 py-3 rounded text-white shadow
            ${loadingAI ? "bg-gray-400" : "bg-purple-500 hover:bg-purple-600"}
          `}
        >
          {loadingAI
            ? "Generating AI Plan..."
            : aiPlan
            ? "Regenerate Plan"
            : "Generate AI Plan"}
        </button>
      </div>
    </div>
  )}
</div> 
)}