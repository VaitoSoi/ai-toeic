import { PenTool } from "lucide-react";

function Header() {
    return <div className="flex flex-col lg:flex-row bg-slate-900 p-5 xl:pl-10 text-white font-bold text-3xl gap-2 items-center">
        <p className="flex flex-row gap-2 items-center text-2xl lg:text-3xl">
            <PenTool />
            <a href="/">TOEIC Writing Platform</a>
        </p>
        <span className="hidden lg:flex lg:text-2xl font-normal lg:ml-auto">
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