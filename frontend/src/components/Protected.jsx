import React, { useEffect, useState } from "react";
import axios from "axios";
import '../style.css';
import Upload from "./Upload";
import Chat from "./Chat";


function Protected() {
    const [message, setMessage] = useState("");
    const [showChat, setShowChat] = useState(false);

    useEffect(() => {
        const fetchProtected = async () => {
            try {
                const token = localStorage.getItem("token");
                const res = await axios.get("http://localhost:5000/protected", {
                    headers: { Authorization: `Bearer ${token}` },
                });
                // setMessage(res.msg);
                // console.log("message: " + res.data.msg)
            } catch {
                window.location = "/signin";
                alert("Session Expired. Please Login Again")

            }
        };
        fetchProtected()
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("email");
        window.location.href = "/signin";
    };

    return (

        <div className="app-container">
            <button className="logout-button" onClick={handleLogout}>
                Logout
            </button>
            <h1>Brain Tumor Detection Chatbot</h1>
            <Upload onDetectionComplete={() => setShowChat(true)} />
            {showChat && <Chat />}
        </div>

    );
}

export default Protected;
