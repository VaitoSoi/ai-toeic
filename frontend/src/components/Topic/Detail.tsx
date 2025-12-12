import api from "@/lib/api";
import type { Submission, Topic } from "@/lib/typing";
import axios from "axios";
import { useCallback, useEffect, useState } from "react";
import { error, success } from "../Toast";
import { useNavigate } from "react-router";
import { ChevronLeft, Mail, NotebookText, Plus, Trash, History, Calendar, ChevronRight } from "lucide-react";
import { Skeleton } from "../ui/skeleton";
import Markdown from "react-markdown";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "../ui/alert-dialog";

function Detail({ topicId: id, preloadedData }: { topicId: string, preloadedData?: Topic }) {
    const navigator = useNavigate();
    const [topic, setTopic] = useState<Topic | undefined>(preloadedData);
    // const deleteTopic

    const getTopic = useCallback(async () => {
        try {
            const response = await api.get<Topic>(`/topic?id=${id}`);
            setTopic({
                ...response.data,
                submissions: await Promise.all(
                    response.data.submissions.map(async (sub) =>
                        (await api.get<Submission>(`/submission?id=${sub.id}`)).data
                    )
                )
            });
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Topic not found >:(");
                navigator("/", { viewTransition: true });
            }
        }
    }, [id, navigator]);
    useEffect(() => !topic ? void getTopic() : undefined, [topic, getTopic]);

    const deleteThis = useCallback(async () => {
        try {
            await api.delete<Topic>(`/topic?id=${id}`);
            navigator("/", { viewTransition: true });
            success(`Deleted topic ${topic?.summary?.summary}`);
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Topic not found >:(");
                navigator("/", { viewTransition: true });
            }
        }
    }, [id, navigator, topic]);

    return <div className="w-full h-full flex flex-col overflow-hidden">
        <AlertDialog>
            <div className="w-2/3 h-full flex flex-col mx-auto gap-10 py-10 overflow-y-auto">{topic ? <>
                <div className="flex flex-col gap-2">
                    <div
                        className="w-fit p-4 flex flex-row items-center text-slate-400 hover:text-slate-800 cursor-pointer transition-all duration-200"
                        onClick={() => navigator("/", { viewTransition: true })}
                    >
                        <ChevronLeft className="size-7" />
                        <p className="text-lg">Go back to dashboard</p>
                    </div>
                    <div className="flex flex-col gap-5 w-full p-5 border-2 border-slate-200 rounded-md">
                        <div className="flex flex-row items-center gap-5 w-full">
                            <div className="size-fit rounded-xl p-5 bg-slate-300">
                                {topic.part == "2" ? <Mail strokeWidth={1.9} className="size-10" /> : <NotebookText strokeWidth={1.9} className="size-10" />}
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold">{topic.summary?.summary}</h1>
                                <p className="text-xl">{topic.part == "2" ? "Q6 - 7 Response to an email" : "Q8 Opinion essay"} • {topic.submissions.length} attemp(s)</p>
                            </div>
                            <div className="flex flex-row gap-2 ml-auto mr-5">
                                <button
                                    className="hover:bg-blue-400 p-4 rounded-md flex flex-row items-center gap-2 cursor-pointer transition-all duration-200"
                                    onClick={() => navigator(`/topic/${topic.id}/submit`, { viewTransition: true, state: JSON.stringify(topic) })}
                                >
                                    <Plus strokeWidth={3} className="size-7" />
                                    <p className="text-lg font-normal">Write new essay</p>
                                </button>
                                <AlertDialogTrigger asChild>
                                    <button className="hover:bg-red-400 p-4 rounded-md flex flex-row items-center cursor-pointer transition-all duration-200">
                                        <Trash strokeWidth={3} className="size-7" />
                                    </button>
                                </AlertDialogTrigger>
                            </div>
                        </div>
                        <div className="w-full text-lg whitespace-pre-wrap">
                            <Markdown>{topic.question}</Markdown>
                        </div>
                    </div>
                </div>
                <div className="flex flex-col gap-3">
                    <div className="flex flex-row items-center gap-2">
                        <History className="size-10" />
                        <h1 className="text-2xl font-bold">Submission history</h1>
                    </div>
                    <div className="grid grid-cols-1 gap-2">{
                        topic.submissions.length
                            ? topic.submissions.map((submission) =>
                                <div
                                    className="w-full h-fit p-5 flex flex-row items-center gap-5 border-2 hover:border-blue-300 transition-all duration-200 rounded-md group cursor-pointer"
                                    onClick={() => navigator(`/topic/${topic.id}/submission/${submission.id}`, { viewTransition: true })}
                                >
                                    <div className="flex flex-row items-center gap-2 text-slate-500">
                                        <Calendar />
                                        <p>{new Date(submission.created_at).toDateString()}</p>
                                    </div>
                                    {submission.review ? <>
                                        <h1 className="text-xl font-medium group-hover:text-blue-600 transition-all duration-200">{submission.review.summary_feedback}</h1>
                                        <div className="ml-auto flex flex-col items-center w-40">
                                            <p className="text-xl font-bold">{submission.review?.score_range
                                                ? `${submission.review.score_range[0]} - ${submission.review?.score_range[1]}`
                                                : "Evaluating"
                                            }</p>
                                            <p className="text-slate-500 uppercase font-bold">Score</p>
                                        </div>
                                    </> : <h1 className="text-xl font-medium group-hover:text-blue-600 transition-all duration-200">Unfinished draft</h1>}
                                    <ChevronRight className="size-0 group-hover:size-9 group-hover:text-blue-600 transition-all duration-200" />
                                </div>)
                            : <div className="w-full p-15 flex flex-col items-center border-2 rounded-md">
                                <h1 className="text-2xl">No submission :(</h1>
                            </div>
                    }</div>
                </div>
            </> : <Skeleton className="w-full h-2/3" />}
            </div>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                        This action cannot be undone. 
                        This will permanently delete this topic and all essays belong to it.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                        className="bg-red-400/70 text-black hover:bg-red-600/90 hover:text-white focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60"
                        onClick={() => deleteThis()}
                    >Continue</AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    </div>;
}

export default Detail;
