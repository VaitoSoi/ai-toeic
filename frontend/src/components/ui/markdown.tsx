import { cn } from "@/lib/utils";
import ReactMarkdown, { type Options } from "react-markdown";

export const Markdown = (prop: Options) => <ReactMarkdown
    components={{
        h1: (prop) => <h1
            className={cn("font-bold text-2xl", prop.className)}
            {...prop}
        >{prop.children}</h1>,
        h2: (prop) => <h2
            className={cn("font-bold text-xl", prop.className)}
            {...prop}
        >{prop.children}</h2>,
        h3: (prop) => <h3
            className={cn("font-semibold text-xl", prop.className)}
            {...prop}
        >{prop.children}</h3>,
        ul: (prop) => <ul
            className={cn("flex flex-col space-0", prop.className)}
            {...prop}
        >{prop.children}</ul>
    }}
    {...prop}
/>