import axios from "axios";
import { useCallback, useEffect, useRef, useState } from "react";
import { error } from "../Toast";
import { useNavigate } from "react-router";
import { Bug, Check, ChevronLeft, ChevronsLeftRightEllipsis, Clock, Sparkle } from "lucide-react";
import { BarLoader } from "react-spinners";
import Markdown from "react-markdown";
import { apiGetTopic, apiRequestReview, apiSubmitSubmission, type SlicedTopic } from "@/api";
import { BACKEND_URL } from "@/api/client.gen";

function Submit({ topicId: id, preloadedData }: { topicId: string, preloadedData?: SlicedTopic }) {
    const navigator = useNavigate();
    const [topic, setTopic] = useState<SlicedTopic | undefined>(preloadedData || undefined);
    const [status, setStatus] = useState<"error" | "not_confirmed" | "writing" | "sending" | "sent">("not_confirmed");
    const topicReloadTimer = useRef<any>(null);

    const getTopic = useCallback(async () => {
        try {
            const response = await apiGetTopic({ query: { id } });
            if (!response.data)
                return setStatus("error");
            if (response.data.status == "done" && !response.data.questions?.at(0))
                return setStatus("error");
            setTopic(response.data);
            if (response.data.status != "pending")
                clearInterval(topicReloadTimer.current);
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
            return;
        if (topic && topic.status != "pending")
            return;
        topicReloadTimer.current = setTimeout(() => void getTopic(), 1000);
        return () => clearTimeout(topicReloadTimer.current);
    }, [preloadedData, topic, getTopic]);

    return <div className="flex flex-col items-center h-full w-full min-h-0">{!topic
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
                : topic.status == "service_failed"
                    ? <div className="m-auto flex flex-col items-center gap-5">
                        <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                            <ChevronsLeftRightEllipsis className="w-10 h-10 text-red-500 animate-pulse" />
                        </div>
                        <div className="flex flex-col items-center">
                            <h1 className="text-3xl font-bold">Service Failure</h1>
                            <p className="text-xl text-center lg:p-0">
                                The AI provider returns unexpected code (not 200 or not SUCCESS)<br />
                                Please take a look at the server console and API console then try again later
                            </p>
                        </div>
                    </div>
                    : <div className="m-auto flex flex-col items-center gap-5">
                        <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                            <Bug className="w-10 h-10 text-red-500 animate-pulse" />
                        </div>
                        <div className="flex flex-col items-center">
                            <h1 className="text-3xl font-bold">Failed to Generate Topic</h1>
                            <p className="text-xl text-center lg:p-0">
                                There is an error occured while generating topic<br />
                                Please look at the server console and try again
                            </p>
                        </div>
                    </div>
            : status != "writing"
                ? status == "not_confirmed"
                    ? <div className="lg:w-2/3 flex flex-col text-lg my-auto mx-10 lg:m-auto p-5 border-2 rounded-md">
                        <h1 className="text-xl font-bold">Direction</h1>
                        {topic.part == "1"
                            ? <p>
                                In this part of the test, you will write ONE sentence that is based on a picture. With each picture, you will be given TWO words or phrases that you must use in your sentence.<br />
                                You can change the forms of the words and you can use the words in any order.<br />
                                Your sentence will be scored on the appropriate use of grammar, and the relevance of the sentence to the picture.<br />
                                You will have eight minutes to complete this part of the test.<br />
                            </p>
                            : topic.part == "2"
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
                            onClick={() => setStatus("writing")}
                        >Start writing</button>
                    </div>
                    : <div className="m-auto">{
                        status == "sending"
                            ? <div className="flex flex-col items-center gap-5">
                                <h1 className="text-3xl font-bold">Sending submission</h1>
                                <BarLoader width={300} />
                            </div>
                            : status == "sent"
                                ? <div className="flex flex-col items-center gap-5">
                                    <div className="rounded-full p-2 text-white bg-green-600"><Check strokeWidth={3} className="size-15" /></div>
                                    <div className="flex flex-col items-center gap-2">
                                        <h1 className="text-3xl font-bold">Sent submission</h1>
                                        <p className="text-xl">Redirect to review page after 5s</p>
                                    </div>
                                </div>
                                : <div className="flex flex-col items-center gap-5">
                                    <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                                        <Bug className="w-10 h-10 text-red-500 animate-pulse" />
                                    </div>
                                    <div className="flex flex-col items-center">
                                        <h1 className="text-3xl font-bold">Failed to get topic</h1>
                                        <p className="text-xl px-10 text-center lg:p-0">There is an error occured while fetching topic</p>
                                        <p className="text-xl text-center lg:p-0">Please look at the console or reload page</p>
                                    </div>
                                </div>
                    }</div>
                : <div className="lg:w-9/10 h-full flex flex-col gap-5 py-5 lg:py-10">
                    <div
                        className="w-fit flex px-4 flex-row items-center text-slate-400 hover:text-slate-800 cursor-pointer transition-all duration-200"
                        onClick={() => navigator(`/topic/${topic.id}`, { viewTransition: true })}
                    >
                        <ChevronLeft className="size-7" />
                        <p className="text-lg">Cancel & Go back</p>
                    </div>
                    {topic.part == "1"
                    ? <UseP1Submission topic={topic} setStatus={setStatus} />
                        : <P23Submission topic={topic} setStatus={setStatus} />}
                </div>
    }</div>;
}

function UseP23Submission({ topic, setStatus }: { topic: SlicedTopic, setStatus: (status: any) => void }) {
    const navigator = useNavigate();
    const [text, setText] = useState<string>("");
    const [timeLeft, setTimeLeft] = useState<number>(0);
    const submissionTimer = useRef<any>(null);

    useEffect(() => setTimeLeft(topic.part == "2" ? 10 * 60 : 30 * 60), [topic.part]);

    useEffect(() => {
        submissionTimer.current = setTimeout(
            () => timeLeft > 0
                ? setTimeLeft(timeLeft => timeLeft -= 1)
                : undefined,
            1000
        );
        return () => clearTimeout(submissionTimer.current);
    }, [timeLeft]);

    const send = useCallback(async (text: string) => {
        if (!topic) return;
        setStatus("sending");
        try {
            const response = await apiSubmitSubmission({ query: { part: topic.part, topic_id: topic.id }, body: { submission: text } });
            if (!response.data)
                return setStatus("error");
            await apiRequestReview({ query: { submission_id: response.data.id } });
            setStatus("sent");
            setTimeout(() => navigator(`/topic/${topic.id}/submission/${response.data.id}`), 5000);
        } catch (err) {
            console.error(err);
        }
    }, [topic, navigator, setStatus]);



    return <div className="flex flex-col lg:flex-row lg:gap-2 h-full w-full min-h-0">
        <div className="lg:flex-2 flex flex-col p-5 border-2 lg:rounded-md gap-2 ">
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
                    <div className="text-xl whitespace-pre-wrap overflow-y-auto"><Markdown>{topic.questions![0].question}</Markdown></div>
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
    </div>;
}

function UseP1Submission({ topic, setStatus }: { topic: SlicedTopic, setStatus: (status: any) => void }) {
    const navigator = useNavigate();
    const [texts, setTexts] = useState<Record<string, string>>(
        Object.fromEntries(topic.questions!.map((val) => [val.file, ""]))
    );
    const [timeLeft, setTimeLeft] = useState<number>(0);
    const submissionTimer = useRef<any>(null);

    useEffect(() => setTimeLeft(8 * 60), []);

    useEffect(() => {
        submissionTimer.current = setTimeout(
            () => timeLeft > 0
                ? setTimeLeft(timeLeft => timeLeft -= 1)
                : undefined,
            1000
        );
        return () => clearTimeout(submissionTimer.current);
    }, [timeLeft]);

    const send = useCallback(async () => {
        if (!topic) return;
        setStatus("sending");
        try {
            const response = await apiSubmitSubmission({
                query: { part: topic.part, topic_id: topic.id },
                body: Object.entries(texts).map(val => ({ file: val[0], submission: val[1] }))
            });
            if (!response.data)
                return setStatus("error");
            await apiRequestReview({ query: { submission_id: response.data.id } });
            setStatus("sent");
            setTimeout(() => navigator(`/topic/${topic.id}/submission/${response.data.id}`), 5000);
        } catch (err) {
            console.error(err);
        }
    }, [topic, texts, navigator, setStatus]);



    return <div className="lg:w-full flex flex-col p-5 border-2 lg:rounded-md gap-5 ">
                <div className="flex flex-row items-center gap-5 ">
                    <h1 className="w-fit p-2 bg-violet-200 rounded-sm text-violet-700 text-sm font-bold uppercase">Describe given images</h1>
                    <div className="flex flex-row items-center gap-2 text-slate-600">
                        <Clock className="size-7" />
                        <p className="font-semibold text-xl">{Math.floor(timeLeft / 60)}:{timeLeft % 60 < 10 ? "0" : ""}{timeLeft % 60}</p>
                    </div>
                </div>
                <div className="flex flex-row gap-10">{topic.questions!.map(val =>
                    <div className="w-100 p-4 rounded-md border-2 flex flex-col items-center gap-3">
                        <img className="rounded-md" src={`${BACKEND_URL}/file/${val.file}`} />
                        <p className="text-xl">{val.keywords!.join(" / ")}</p>
                        <input
                            className="border-2 rounded-md px-2 py-1"
                            placeholder="Your sentence"
                            value={texts[val.id]}
                            onChange={(event) => setTexts((prev) => ({ ...prev, [val.file!]: event.target.value }))}
                        />
                    </div>
                )}</div>
                <div className="flex flex-row items-center">
                    <button
                        className="ml-auto px-3 py-2 rounded-md text-white disabled:bg-blue-200 disabled:cursor-not-allowed enabled:bg-blue-600 enabled:cursor-pointer"
                        disabled={!!Object.values(texts).filter(val => val.length == 0).length}
                        onClick={() => send()}
                    >
                        Submit for review
                    </button>
                </div>
    </div>;
}

export default Submit;
