import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import "./login.css";
import { NavLink } from "react-router-dom";
import { toast } from "react-hot-toast";
import { encrypt } from "./encryption";

const SignUp = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isLoading2, setIsLoading2] = useState(false);
  const [serverError, setServerError] = useState("");
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [otpInput, setOtpInput] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpBtnName, setotpBtnName] = useState("Get OTP");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm();

  const email = watch("email");
  const password = watch("password");

  useEffect(() => {
    if (otpInput.length === 6) verifyOtp();
  }, [otpInput]);

  const sendOtp = async () => {
    if (!email) {
      setServerError("Please enter email first.");
      setTimeout(() => setServerError(""), 2000);
      return;
    }

    try {
      setIsLoading2(true);
      const response = await fetch("http://localhost:5000/get-otp", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ email }),
        headers: { "Content-Type": "application/json" },
      });
      if (response.status === 429) {
        setServerError("Failed to send OTP. Too many requests. Please try after few minutes");
        setIsLoading2(false);
        setTimeout(() => setServerError(""), 3000);
        return;
      }
      const result = await response.json();
      if (result.success) {
        setOtpSent(true);
        toast.success("OTP Sent to E-Mail");
        setIsLoading2(false);
      } else {
        setServerError(result.msg || "Failed to send OTP.");
        setIsLoading2(false);
        setTimeout(() => setServerError(""), 2000);
      }
    } catch (error) {
      setServerError("Error sending OTP.");
      setIsLoading2(false)
      setTimeout(() => setServerError(""), 2000);
    }
  };

  const verifyOtp = async () => {
    setotpBtnName("Verifing...")
    try {
      const response = await fetch("http://localhost:5000/verify-otp", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ otp: otpInput }),
        headers: { "Content-Type": "application/json" },
      });

      const result = await response.json();
      if (result.success) {
        setOtpVerified(true);
        toast.success("OTP Verified!");
        setotpBtnName("Verified...")
      } else {
        setOtpVerified(false);
        setServerError(result.msg || "Invalid OTP.");
        setotpBtnName("Error!")
        setTimeout(() => setServerError(""), 2000);
      }
    } catch (error) {
      setServerError("Error verifying OTP.");
      setotpBtnName("Error!")
      setTimeout(() => setServerError(""), 2000);
    }
  };

  const onSubmit = async (data) => {
    if (!otpVerified) return;

    setServerError("");
    setIsLoading(true);

    try {
      const { ciphertext, iv } = encrypt(data.password);

      const encryptedPayload = {
        email: data.email,
        password: ciphertext,
        iv: iv
      };
      // console.log("Data: ", data);
      // console.log("Encrypted Payload: ", encryptedPayload);

      const response = await fetch("http://localhost:5000/signup", {
        method: "POST",
        body: JSON.stringify(encryptedPayload),
        headers: { "Content-Type": "application/json" },
      });

      const result = await response.json();

      if (result.success === "false") {
        setServerError(result.msg || "An error occurred.");
        setTimeout(() => setServerError(""), 2000);
        setIsLoading(false);
        reset();
        setotpBtnName("Get OTP")
        setOtpInput("");
        return;
      }

      setShowSuccessMessage(true);
      setTimeout(() => {
        setShowSuccessMessage(false);
        reset();
        setotpBtnName("Get OTP")
        setOtpVerified(false);
        setOtpInput("");
      }, 1500);
    } catch (error) {
      setServerError("Signup failed.");
      setTimeout(() => setServerError(""), 2000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="signup-container-signup signup-container">
      <div className="signup">
        <div className="signupForm">
          <h3>Sign Up</h3>

          {showSuccessMessage && (
            <div className="green msgs">User created! Now login.</div>
          )}
          {serverError && <div className="red msgs">{serverError}</div>}

          <form className="form" onSubmit={handleSubmit(onSubmit)}>
            <input
              type="email"
              placeholder="Enter Email"
              {...register("email", {
                required: { value: true, message: "Please Enter Email" },
              })}
            />
            {errors.email && (
              <p className="red msgs">{errors.email.message}</p>
            )}

            <input
              type="password"
              placeholder="Enter Password"
              {...register("password", {
                required: { value: true, message: "Please Enter Password" },
                minLength: {
                  value: 3,
                  message: "Password must be at least 3 characters",
                },
                maxLength: {
                  value: 10,
                  message: "Password must be less than 10 characters",
                },
              })}
            />
            {errors.password && (
              <p className="red msgs">{errors.password.message}</p>
            )}

            <div className="otp-row">
              <input
                type="text"
                placeholder="Enter 6-digit OTP"
                value={otpInput}
                onChange={(e) => setOtpInput(e.target.value)}
                maxLength={6}
                className="otp-input"
              />
              <button
                disabled={otpVerified}
                type="button"
                className="send-otp-btn"
                onClick={sendOtp}
              >
                {otpBtnName}{" "}{isLoading2 && (
                  <i className="fa-solid fa-spinner fa-spin"></i>
                )}
              </button>
            </div>

            <button type="submit" disabled={!otpVerified || isLoading}>
              Sign Up{" "}
              {isLoading && (
                <i className="fa-solid fa-spinner fa-spin"></i>
              )}
            </button>
          </form>
        </div>
        <p>
          Already have an account? <NavLink to="/signin">Sign In</NavLink>
        </p>
      </div>
    </div>
  );
};

export default SignUp;
