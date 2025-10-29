import axios from "axios";

// Create and export axios instance with base URL configuration
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
});

