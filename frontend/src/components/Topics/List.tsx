import api from "@/lib/api";
import type { Topic } from "@/lib/typing";
import { reduceWords } from "@/lib/utils";
import { Mail, NotebookText, Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router";

function List() {
    const navigator = useNavigate();
    const [topics, setTopics] = useState<(Topic & { icon: typeof Mail })[]>();

    const getTopics = useCallback(async () => {
        try {
            const response = await api.get<Topic[]>("/topics");
            setTopics(
                response.data.map(val => ({
                    ...val,
                    icon: val.part == "2" ? Mail : NotebookText
                }))
            );
        } catch (error) {
            console.error(error);
        }
    }, []);
    useEffect(() => void getTopics(), [getTopics]);

    return <div className="w-full h-fit p-5 lg:pl-10 flex flex-col">
        <h1 className="text-3xl font-semibold">🖊️ Essays</h1>
        <h2 className="text-xl font-normal ml-12">Select a writing section to begin your training session</h2>
        <div className="grid xl:grid-cols-4 lg:grid-cols-3 md:grid-cols-2 grid-cols-1 py-5 gap-5">
            {topics
                ? topics.map((val) => <div
                    className="min-h-65 border-2 rounded-md overflow-hidden hover:shadow-md transition-shadow duration-200 group cursor-pointer"
                    onClick={() => navigator(`/topic/${val.id}`, { viewTransition: true })}
                >
                    <div className="w-full h-2" />
                    <div className="p-6 flex flex-col gap-3">
                        <val.icon strokeWidth={2} className={`size-15 p-2 bg-slate-300/30 rounded-md`} />
                        <h2 className="text-2xl font-bold group-hover:text-blue-500 transition-colors duration-200">{reduceWords(val.summary?.summary || "No title", 25)}</h2>
                        <p className="text-lg font-normal text-slate-700">{val.summary?.description}</p>
                    </div>
                </div>)
                : <></>
            }
            <div
                className="min-h-65 flex border-2 rounded-md border-slate-200 hover:border-slate-500 transition-all duration-150 border-dashed group cursor-pointer"
                onClick={() => navigator("/topic/new", { viewTransition: true })}
            >
                <div className="m-auto flex flex-col items-center">
                    <Plus className="size-1 opacity-0 group-hover:opacity-100 group-hover:size-10 transition-all duration-150" />
                    <p className="text-xl text-slate-400 group-hover:text-slate-800 transition-all duration-150">Generate new topic</p>
                </div>
            </div>
        </div>
    </div>;
}

export default List;