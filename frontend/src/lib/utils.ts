import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function reduceWords(str: string, maxLength: number = 25) {
    if (str.length <= maxLength) return str;
    let tempStr = "";
    for (const word of str.split(" "))
        if ((tempStr + word).length > maxLength)
            return tempStr + "...";
        else
            tempStr += " " + word;
    return tempStr;
}
