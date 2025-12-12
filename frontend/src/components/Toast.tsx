import { toast } from "sonner";

export const error = (error: string) =>
    toast.error("An error occurred", {
        position: "top-right",
        description: error,
        richColors: true
    });

export const success = (message: string) =>
    toast.success(message, {
        position: "top-right",
        richColors: true
    });

export const warning = (message: string) =>
    toast.warning(message, {
        position: "top-right",
        richColors: true
    });

export const info = (message: string) =>
    toast.info(message, {
        position: "top-right",
        richColors: true
    });