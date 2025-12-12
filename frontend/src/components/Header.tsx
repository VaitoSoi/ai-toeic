import { PenTool } from "lucide-react";

function Header() {
    return <div className="flex flex-row bg-slate-900 p-5 pl-10 text-white font-bold text-3xl gap-2 items-center">
        <p className="flex flex-row gap-2 items-center">
            <PenTool />
            <a href="/">TOEIC Writing Platform</a>
        </p>
        <span className="text-2xl font-normal ml-auto">
            By <a
                href="https://github.com/vaitosoi"
                className="hover:text-blue-500 transition-all duration-200"
            >Vaito</a> with <a
                href="https://openrouter.ai/"
                className="hover:text-blue-500 transition-all duration-200"
            >OpenRouter</a></span>
    </div>;
}

export default Header;