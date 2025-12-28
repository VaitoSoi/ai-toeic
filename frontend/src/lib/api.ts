import axios from "axios";

export default axios.create({
    baseURL: import.meta.env.MODE == "production" ? "/api" : import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"
});
