import React, { useState } from "react";
import "./login.css";
import { NavLink, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useUser } from "./UserContext";
import { encrypt } from "./encryption";

const Login = () => {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState("");
  const { setEmail } = useUser();

  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm();

  const onSubmit = async (data) => {
    // console.log("data: ",data)
    try {
      const { ciphertext, iv } = encrypt(data.password);

      const encryptedPayload = {
        email: data.email,
        password: ciphertext,
        iv: iv
      };

      // console.log("Encrypted Payload: ", encryptedPayload)

      const response = await fetch("http://localhost:5000/login", {
        method: "POST",
        body: JSON.stringify(encryptedPayload),
        headers: { "Content-Type": "application/json" },
      });
      const json = await response.json();
      if (json.token) {
        localStorage.setItem("token", json.token);
        localStorage.setItem("email", data.email);
        // setEmail(data.email);
        navigate("/");
      } else {
        setServerError(json.msg || "Login failed");
        setTimeout(() => setServerError(""), 2000);
      }
    } catch (e) {
      setServerError("Server error. Please try again later.");
      setTimeout(() => setServerError(""), 2000);
    }
  };

  return (
    <>
      <div className="signup-container-signin signup-container">
        <div className="signup">
          <div className="signupForm">
            <h3>Login</h3>
            {serverError && <div className="red msgs">{serverError}</div>}
            <form className="form" onSubmit={handleSubmit(onSubmit)}>
              <input
                type="email"
                placeholder="Enter Email"
                {...register("email", { required: true })}
              />
              {errors.email && <p className="error-msg">Email is required</p>}
              <input
                type="password"
                placeholder="Enter Password"
                {...register("password", { required: true })}
              />
              {errors.password && <p className="error-msg">Password is required</p>}
              <button type="submit" disabled={isSubmitting}>
                Login
              </button>
            </form>
          </div>
          <p>
            Don’t have an account? <NavLink to="/signup">Sign Up</NavLink>
          </p>
        </div>
      </div>
    </>
  );
};

export default Login;
