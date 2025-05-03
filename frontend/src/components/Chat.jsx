import React, { useState } from "react";
import axios from "axios";
import ReactMarkdown from 'react-markdown';
import {encrypt, decrypt} from './encryption';

export default function Chat() {
    const [query, setQuery] = useState("");
    const [response, setResponse] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleQuery = async () => {
        setIsLoading(true);
        const tumor_info = JSON.parse(localStorage.getItem("tumor_info") || "[]");
        const tumor_count = JSON.parse(localStorage.getItem("tumor_count") || "[]");
        const token = localStorage.getItem("token");
        const { ciphertext, iv } = encrypt(query);
        // console.log("Encrypted Query: ", ciphertext);
        try {
            const res = await axios.post("http://localhost:5000/chat", {
                query: ciphertext,
                iv: iv,
                tumor_info,
                tumor_count
            }, {
                headers: {
                    Authorization: `Bearer ${token}`, // Secure header
                }
            }
            );
            // console.log("Status Code", res.status)
            // console.log("Encrypted Respnse: ", res.data.response);
            const decryptedResponse = decrypt(res.data.response, res.data.iv);
            // console.log("Decrypted Response: ", decryptedResponse)
            setResponse(decryptedResponse);
            setIsLoading(false);
        } catch (err) {
            console.error("Chat error:", err.response?.data || err.message);
            alert("Error: " + (err.response?.data?.error || err.message));
            setIsLoading(false);
        }
    };

    return (
        <div className="chat-section">
            <input
                type="text"
                placeholder="Ask about the tumor..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
            />
            <button onClick={handleQuery}>Ask {isLoading && <i className="fa-solid fa-spinner fa-spin"></i>}</button>
            <p className="bot-response"> {response && <ReactMarkdown>{response}</ReactMarkdown>}</p>

        </div>
    );
}
