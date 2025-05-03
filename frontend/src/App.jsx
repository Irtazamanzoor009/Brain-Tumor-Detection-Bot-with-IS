import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Signup from "./components/Signup";
import Login from "./components/Login";
import Protected from "./components/Protected";
import { Toaster } from "react-hot-toast";

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
      </Routes>
    </Router>
  );
}

export default App;
