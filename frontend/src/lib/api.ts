import axios from "axios";

export default axios.create({
    baseURL: import.meta.env.MODE == "production" ? "/api" : "http://localhost:8000"
});
