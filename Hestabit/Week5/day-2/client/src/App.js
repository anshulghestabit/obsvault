import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("Loading...");

  useEffect(() => {
    fetch("/api")
        .then((res) => res.text())
        .then((data) => setMessage(data))
        .catch(() => setMessage("Failed to connect to backend"));
  }, []);

  return (
      <div className="App">
        <header className="App-header">
          <h1>Docker Compose Day 2</h1>
          <p>{message}</p>
        </header>
      </div>
  );
}

export default App;