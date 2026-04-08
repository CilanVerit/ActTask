import { useState } from "react";
import Login from "./Login";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem("token")
  );

  if (!isLoggedIn) {
    return <Login onLogin={() => setIsLoggedIn(true)} />;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">
        Logged in successfully
      </h1>
    </div>
  );
}