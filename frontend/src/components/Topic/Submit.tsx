import api from "@/lib/api";
import type { Submission, Topic } from "@/lib/typing";
import axios from "axios";
import { useCallback, useEffect, useRef, useState } from "react";
import { error } from "../Toast";
import { useNavigate } from "react-router";
import { Bug, Check, ChevronLeft, Clock, Sparkle } from "lucide-react";
import { BarLoader } from "react-spinners";
import Markdown from "react-markdown";

function Submit({ topicId: id, preloadedData }: { topicId: string, preloadedData?: Topic }) {
    const navigator = useNavigate();
    const [topic, setTopic] = useState<Topic | undefined>(preloadedData);
    const [text, setText] = useState<string>("");
    const [timeLeft, setTimeLeft] = useState<number>(0);
    const [confirmed, setConfirm] = useState<boolean>(false);
    const [submissionStatus, setSubmissionStatus] = useState<"sending" | "sent">();
    const topicReloadTimer = useRef<any>(null);
    const submissionTimer = useRef<any>(null);

    const getTopic = useCallback(async () => {
        try {
            const response = await api.get<Topic>(`/topic?id=${id}`);
            setTopic(response.data);
            if (response.data.status != "pending") {
                if (response.data.status == "done")
                    setTimeLeft((response.data.part == "2" ? 10 : 30) * 60);
                clearInterval(topicReloadTimer.current);
            }
        } catch (err) {
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Topic not found >:(");
                navigator("/", { viewTransition: true });
            }
            console.error(err);
        }
    }, [id, navigator]);
    useEffect(() => {
        if (preloadedData && preloadedData.status == "done")
            return void setTimeLeft((preloadedData.part == "2" ? 10 : 30) * 60);
        if (topic && topic.status != "pending")
            return;
        topicReloadTimer.current = setInterval(() => void getTopic(), 1000);
        return () => clearInterval(topicReloadTimer.current);
    }, [preloadedData, topic, getTopic]);
    useEffect(() => {
        submissionTimer.current = setInterval(
            () => timeLeft > 0 && confirmed
                ? setTimeLeft(timeLeft => timeLeft -= 1)
                : undefined,
            1000
        );
        return () => clearInterval(submissionTimer.current);
    }, [timeLeft, confirmed]);

    const send = useCallback(async (text: string) => {
        if (!topic) return;
        setSubmissionStatus("sending");
        try {
            const response = await api.post<Submission>(`/submission?topic_id=${topic.id}`, { submission: text });
            await api.post(`/review?submission_id=${response.data.id}`);
            setSubmissionStatus("sent");
            setTimeout(() => navigator(`/topic/${topic.id}/submission/${response.data.id}`), 5000);
        } catch (err) {
            console.error(err);
        }
    }, [topic, navigator]);

    return <div className="flex flex-col items-center w-full flex-1 min-h-0">{!topic
        ? <div className="m-auto">
            <div className="flex flex-col items-center gap-5">
                <h1 className="text-3xl font-bold">Loading topic</h1>
                <BarLoader width={300} />
            </div>
        </div>
        : topic.status != "done"
            ? topic.status == "pending"
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
                : <div className="m-auto flex flex-col items-center gap-5">
                    <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                        <Bug className="w-10 h-10 text-red-500 animate-pulse" />
                    </div>
                    <div className="flex flex-col items-center">
                        <h1 className="text-3xl font-bold">Failed to generate topic</h1>
                        <p className="text-xl px-10 text-center lg:p-0">There is an error occured while generating topic</p>
                        <p className="text-xl text-center lg:p-0">Please look at the server console and try again</p>
                    </div>
                </div>
            : !confirmed
                ? <div className="lg:w-2/3 flex flex-col text-lg my-auto mx-10 lg:m-auto p-5 border-2 rounded-md">
                    <h1 className="text-xl font-bold">Direction</h1>
                    {topic.part == "2"
                        ? <p>
                            In this part of the test, you will show how well you can write a response to an e-mail.<br />
                            Your response will be scored on the quality and variety of your sentences, vocabulary, and organization.<br />
                            You will have 10 minutes to read and answer each e-mail.
                        </p>
                        : <p>
                            In this part of the test, you will write an essay in response to a question that asks you to state, explain, and support your opinion on an issue. Typically, an effective essay will contain a minimum of 300 words.<br />
                            Your response will be scored on whether your opinion is supported with reasons and/or examples, grammar, vocabulary, and organization.<br />
                            You will have 30 minutes to plan, write, and revise your essay.
                        </p>
                    }
                    <button
                        className="ml-auto mr-5 mt-5 p-2 border-2 rounded-md cursor-pointer"
                        onClick={() => setConfirm(true)}
                    >Start writing</button>
                </div>
                : submissionStatus
                    ? <div className="m-auto">{submissionStatus == "sending"
                        ? <div className="flex flex-col items-center gap-5">
                            <h1 className="text-3xl font-bold">Sending submission</h1>
                            <BarLoader width={300} />
                        </div>
                        : <div className="flex flex-col items-center gap-5">
                            <div className="rounded-full p-2 text-white bg-green-600"><Check strokeWidth={3} className="size-15" /></div>
                            <div className="flex flex-col items-center gap-2">
                                <h1 className="text-3xl font-bold">Sent submission</h1>
                                <p className="text-xl">Redirect to review page after 5s</p>
                            </div>
                        </div>
                    }</div>
                    : <div className="lg:w-9/10 h-full lg:overflow-hidden flex-1 flex flex-col gap-5 py-5 lg:py-10">
                        <div
                            className="w-fit flex flex-row items-center text-slate-400 hover:text-slate-800 cursor-pointer transition-all duration-200"
                            onClick={() => navigator(`/topic/${topic.id}`, { viewTransition: true })}
                        >
                            <ChevronLeft className="size-7" />
                            <p className="text-lg">Cancel & Go back</p>
                        </div>
                        <div className="flex flex-col lg:flex-row lg:gap-2 flex-1 min-h-0">
                            <div className="lg:w-2/5 flex flex-col p-5 border-2 lg:rounded-md gap-2 ">
                                <div className="flex flex-row items-center gap-5 ">
                                    {topic.part == "2"
                                        ? <h1 className="w-fit p-2 bg-green-200 rounded-sm text-green-700 text-sm font-bold uppercase">Response to an email</h1>
                                        : <h1 className="w-fit p-2 bg-blue-200 rounded-sm text-blue-700 text-sm font-bold uppercase">Opinion essay</h1>
                                    }
                                    <div className="flex flex-row items-center gap-2 text-slate-600">
                                        <Clock className="size-7" />
                                        <p className="font-semibold text-xl">{Math.floor(timeLeft / 60)}:{timeLeft % 60 < 10 ? "0" : ""}{timeLeft % 60}</p>
                                    </div>
                                </div>
                                <h1 className="text-2xl font-bold">{topic.summary?.summary}</h1>
                                <div className="text-xl whitespace-pre-wrap overflow-y-auto"><Markdown>{topic.question}</Markdown></div>
                            </div>
                            <div className="lg:w-3/5 flex flex-col border-2 lg:rounded-md">
                                <textarea
                                    className="flex-1 w-full p-6 resize-none focus:outline-none text-slate-800 leading-relaxed overflow-scroll"
                                    placeholder="Start writing your essay here..."
                                    value={text}
                                    onChange={(e) => setText(e.target.value)}
                                    spellCheck="false"
                                    rows={10}
                                />
                                <div className="py-5 px-10 border-t-2 flex flex-row items-center">
                                    <p className="text-slate-500">{text.split(" ").filter(x => x.length).length} word(s)</p>
                                    <button
                                        className="ml-auto px-3 py-2 rounded-md text-white disabled:bg-blue-200 disabled:cursor-not-allowed enabled:bg-blue-600 enabled:cursor-pointer"
                                        // disabled={topic.part == "3" && text.split(" ").filter(x => x.length).length < 250}
                                        onClick={() => send(text)}
                                    >
                                        Submit for review
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
    }</div>;
}

export default Submit;
