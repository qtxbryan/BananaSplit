// hooks/useAuth.js
import { useState, useEffect } from "react";
import {
  login as loginService,
  logout as logoutService,
} from "../services/authService";

const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("user_id");
    if (token && userId) {
      setUser({ user_id: userId });
    }
    setLoading(false);
  }, []);

  const loginUser = async (email, password) => {
    try {
      const { access_token, user_id } = await loginService(email, password);
      setUser({ user_id });
      localStorage.setItem("token", access_token);
      localStorage.setItem("user_id", user_id);
      console.log("Access Token:", access_token);
      console.log("User ID:", user_id);
      return true;
    } catch (error) {
      throw new Error(error.message);
    }
  };

  const logoutUser = () => {
    logoutService();
    setUser(null);
  };

  return { user, loginUser, logoutUser, loading };
};

export default useAuth;