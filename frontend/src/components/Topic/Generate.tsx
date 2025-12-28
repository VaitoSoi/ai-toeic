import { ChevronLeft, ChevronRight, Mail, NotebookText, Sparkle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { BarLoader } from "react-spinners";
import { error } from "../Toast";
import api from "@/lib/api";
import type { Topic } from "@/lib/typing";

function Generate() {
    const navigator = useNavigate();
    const [part, setPart] = useState<2 | 3>();

    const generateTopic = useCallback(async () => {
        try {
            const response = await api.post<Topic>(`/topic?part=${part}`);
            const data = response.data;
            navigator(
                `/topic/${data.id}/submit`,
                { state: JSON.stringify(data) }
            );
        } catch (err) {
            console.error(err);
            error("API Error");
            navigator("/");
        }
    }, [part, navigator]);
    useEffect(() => part == 2 || part == 3 ? void generateTopic() : undefined, [part, generateTopic]);

    return <div className="h-full w-full flex">{
        part
            ? <div className="m-auto">
                <div className="flex flex-col items-center gap-5">
                    <div className="relative">
                        <div className="absolute inset-0 bg-blue-100 rounded-full animate-ping opacity-75"></div>
                        <div className="relative bg-white p-6 rounded-full shadow-lg border ">
                            <Sparkle className="w-10 h-10 text-blue-500 animate-pulse" />
                        </div>
                    </div>
                    <div className="flex flex-col items-center">
                        <h1 className="text-3xl font-bold">Generating topic</h1>
                        <p className="px-10 text-center lg:p-0 text-xl">The AI is crafting a unique prompt based on TOEIC standards</p>
                    </div>
                    <BarLoader width={300} />
                </div>
            </div>
            : <div className="m-auto w-150">
                <div
                    className="w-fit flex py-3 px-3 lg:px-0 flex-row items-center text-slate-400 hover:text-slate-800 cursor-pointer transition-all duration-200"
                    onClick={() => navigator("/", { viewTransition: true })}
                >
                    <ChevronLeft className="size-7" />
                    <p className="text-lg">Go back to dashboard</p>
                </div>
                <div className="lg:border-2 lg:rounded-md p-5">
                    <h1 className="text-2xl font-bold">Pick a part</h1>
                    <h2 className="text-xl font-normal text-slate-400">Select the TOEIC writing part you want to practice:</h2>
                    <div className="w-full mt-4 flex flex-col gap-2">
                        <div
                            className="w-full p-5 flex flex-row items-center gap-5 border-2 rounded-md hover:bg-green-300/20 hover:border-green-300 transition-all duration-200 group cursor-pointer"
                            onClick={() => setPart(2)}
                        >
                            <div className="p-3 rounded-full bg-green-100 text-green-600 group-hover:bg-green-200 transition-colors">
                                <Mail className="size-10" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold group-hover:text-green-800 transition-all duration-200">Part 2</h1>
                                <h2 className="text-lg font-normal text-slate-400">Question 6 - 7 • 10 minutes</h2>
                            </div>
                            <ChevronRight
                                className="hidden lg:flex ml-auto size-10 opacity-0 group-hover:opacity-100 group-hover:translate-x-2 transition-all  duration-200"
                            />
                        </div>
                        <div
                            className="w-full p-5 flex flex-row items-center gap-5 border-2 rounded-md hover:bg-blue-300/20 hover:border-blue-300 transition-all duration-200 group cursor-pointer"
                            onClick={() => setPart(3)}
                        >
                            <div className="p-3 rounded-full bg-blue-100 text-blue-600 group-hover:bg-blue-200 transition-colors">
                                <NotebookText className="size-10" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold group-hover:text-blue-800 transition-all duration-200">Part 3</h1>
                                <h2 className="text-lg font-normal text-slate-400">Question 8 • 30 minutes</h2>
                            </div>
                            <ChevronRight
                                className="hidden lg:flex ml-auto size-10 opacity-0 group-hover:opacity-100 group-hover:translate-x-2 transition-all duration-200"
                            />
                        </div>
                    </div>
                </div>
            </div>
    }</div>;
}

export default Generate;