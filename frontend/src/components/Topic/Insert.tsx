import { ChevronLeft, ChevronRight, Mail, NotebookText, Plus, Lock } from "lucide-react";
import { useCallback, useState } from "react";
import { useNavigate } from "react-router";
import { error } from "../Toast";
import { apiInsertTopic } from "@/api";
import { cn } from "@/lib/utils";

function Insert() {
    const navigator = useNavigate();
    const [part, setPart] = useState<"2" | "3">();
    const [text, setText] = useState<string>();

    const send = useCallback(async () => {
        if (!part || !text) return;
        try {
            const response = await apiInsertTopic({
                query: { part: part },
                body: { question: text }
            });
            const data = response.data!;
            navigator(
                `/topic/${data.id}/submit`,
                { state: JSON.stringify(data) }
            );
        } catch (err) {
            console.error(err);
            error("API Error");
            navigator("/");
        }
    }, [part, text, navigator]);

    return <div className="h-full w-full flex">
        <div className="m-auto h-full xl:h-auto flex flex-col xl:gap-2">
            <div
                className="w-fit flex mt-5 xl:mt-0 p-3 lg:px-0 flex-row items-center text-slate-400 hover:text-slate-800 cursor-pointer transition-all duration-200"
                onClick={() => navigator("/", { viewTransition: true })}
            >
                <ChevronLeft className="size-7" />
                <p className="text-lg">Go back to dashboard</p>
            </div>
            <div className="xl:min-w-300 h-full xl:min-h-150 gap-5 flex flex-col xl:flex-row lg:border-2 lg:rounded-md p-5">
                <div className="flex flex-col flex-1">
                    <h1 className="text-2xl font-bold flex flex-row gap-1 items-center"><Plus strokeWidth={3} /> Insert a Topic</h1>
                    <h2 className="text-xl font-normal text-slate-400">Select the TOEIC writing part you want to insert:</h2>
                    <div className="w-full mt-4 flex flex-col gap-2">
                        <div
                            className={cn(
                                "w-full p-5 flex flex-row items-center gap-5 border-2 rounded-md transition-all duration-200 group cursor-pointer",
                                "hover:bg-green-300/20 hover:border-green-300",
                                part == "2" && "bg-green-300/20 border-green-300"
                            )}
                            onClick={() => setPart("2")}
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
                            className={cn(
                                "w-full p-5 flex flex-row items-center gap-5 border-2 rounded-md transition-all duration-200 group cursor-pointer",
                                "hover:bg-blue-300/20 hover:border-blue-300",
                                part == "3" && "bg-blue-300/20 border-blue-300 "
                            )}
                            onClick={() => setPart("3")}
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
                    <button
                        className="ml-auto mt-2 px-3 py-2 text-xl xl:text-lg rounded-md text-white disabled:bg-blue-200 disabled:cursor-not-allowed enabled:bg-blue-600 enabled:cursor-pointer"
                        disabled={!part || !text?.length}
                        onClick={() => send()}
                    >
                        Send
                    </button>
                </div>
                <div className="flex flex-col flex-1">
                    <h1 className="text-2xl font-bold flex flex-row gap-1 items-center">Put your question here:</h1>
                    {part
                        ? <textarea
                            className="flex-1 border rounded-md p-2 resize-none text-lg focus:outline-none text-slate-800 leading-relaxed overflow-auto"
                            placeholder={
                                (part == "2" ? "Insert an email or a flyer here ✉️" : "Insert an opinion here 🤔") + "\n" + 
                                "Note: Direction is not automatically included, please manually include one :_D\n" + 
                                "P/s: Markdown supported :D"
                            }
                            onChange={(event) => setText(event.target.value)}
                        />
                        : <div className="flex-1 mt-2 bg-slate-100 rounded-md flex">
                            <div className="m-auto flex flex-col items-center">
                                <Lock className="size-10" />
                                <p className="text-xl">Please select target topic part</p>
                            </div>
                        </div>
                    }
                </div>
            </div>
        </div>
    </div>;
}

export default Insert;