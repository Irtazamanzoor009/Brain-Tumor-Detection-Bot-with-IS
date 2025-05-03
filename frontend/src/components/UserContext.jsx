import { createContext, useState, useContext } from "react";

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [email, setEmail] = useState(null);

//   useEffect(() => {
//     const savedEmail = localStorage.getItem("email");
//     if (savedEmail) {
//         setEmail(savedEmail);
//     }
//   }, []);

  return (
    <UserContext.Provider value={{ email, setEmail }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);
