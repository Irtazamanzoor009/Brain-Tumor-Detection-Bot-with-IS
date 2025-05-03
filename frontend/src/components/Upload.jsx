import React, { useState } from "react";
import axios from "axios";
import { encrypt } from "./encryption";

export default function Upload({ onDetectionComplete }) {
    const [image, setImage] = useState(null);
    const [resultUrl, setResultUrl] = useState(null);
    const [tumor_count, settumor_count] = useState(0);
    const [tumor_info, settumor_info] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleUpload = async () => {
        if (!image) {
            alert("Please select an image.");
            return;
        }

        setIsLoading(true);

        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                // console.log(e.target.result);
                const base64Image = e.target.result.split(',')[1];
                const { ciphertext, iv } = encrypt(base64Image);

                const formData = new FormData();
                formData.append("ciphertext", ciphertext);
                formData.append("iv", iv);
                const email = localStorage.getItem("email");
                formData.append("email", email);

                console.log("Form Data: ", formData);
                console.log("Email: ", email)
                // console.log("Cipher Text: ", ciphertext)
                console.log("iv: ", iv);

                const token = localStorage.getItem("token");

                const response = await axios.post("http://localhost:5000/predict", formData, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (response.status === 429) {
                    alert("Too many requests. Try again after few minutes");
                    return;
                }

                const { tumor_info, tumor_count, image: base64Result } = response.data;

                localStorage.setItem("tumor_info", JSON.stringify(tumor_info));
                localStorage.setItem("tumor_count", JSON.stringify(tumor_count));

                settumor_count(tumor_count);
                settumor_info(tumor_info);

                const imageUrl = `data:image/jpeg;base64,${base64Result}`;
                setResultUrl(imageUrl);

                if (onDetectionComplete) onDetectionComplete();
            } catch (err) {
                console.error("Prediction failed:", err);
                alert("Unauthorized or error occurred!");
            } finally {
                setIsLoading(false);
            }
        };

        reader.readAsDataURL(image); // Convert image file to Base64 and trigger `onload`
    };

    return (
        <div className="upload-section">
            <input
                className="input-field"
                type="file"
                onChange={(e) => setImage(e.target.files[0])}
            />
            <button onClick={handleUpload}>
                Upload & Detect {isLoading && <i className="fa-solid fa-spinner fa-spin"></i>}
            </button>
            {resultUrl && <img src={resultUrl} alt="Detection Result" className="result-img" />}
            <p>Number of tumors detected: {tumor_count}</p>
            {tumor_info && tumor_info.length > 0 && (
                <div>
                    {tumor_info.map((tumor, index) => (
                        <div key={index}>
                            Tumor {index + 1}: Confidence = {tumor.confidence.toFixed(2)} <br />
                            Coordinates = ({tumor.box.join(", ")})
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

