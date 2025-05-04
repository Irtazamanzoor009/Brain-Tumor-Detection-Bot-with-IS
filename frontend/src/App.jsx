import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Signup from "./components/Signup";
import Login from "./components/Login";
import Protected from "./components/Protected";
import { Toaster } from "react-hot-toast";
import LogsViewer from "./components/LogsViewer";

function App() {
  return (
    <Router>
      <Toaster
          position="top-center"
          reverseOrder={false}
          toastOptions={{
            style: {
              fontFamily: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
            },
          }}
        />
      <Routes>
        <Route path="/signin" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/" element={<Protected />} />
        <Route path="/logs" element={<LogsViewer />} />

      </Routes>
    </Router>
  );
}

export default App;
