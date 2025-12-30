import type { ReviewAnnotation, Review as ReviewType, Submission } from "@/lib/typing";
import { BookOpen, Bug, ChevronLeft, CircleQuestionMark, MessageSquare, PenTool, Percent, Sparkle, Sparkles } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BarLoader } from "react-spinners";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "../ui/hover-card";
import api from "@/lib/api";
import axios from "axios";
import { error } from "../Toast";
import { useNavigate } from "react-router";
import { cn } from "@/lib/utils";
import { Checkbox } from "../ui/checkbox";

type Annotation = (
    {
        key: string,
        text: string
    } & ({
        isAnnotation: false,
    } | {
        isAnnotation: true,
        color: string,
    } & Omit<ReviewAnnotation, "target_text" | "context_before">)
);

function Review({ submissionId }: { submissionId: string }) {
    const radius = 50;
    const navigator = useNavigate();

    const [mounted, setMounted] = useState(false);

    const [reviewId, setReviewId] = useState<string>();
    const [status, setStatus] = useState<"no_review" | "reviewing" | "failed" | "done" | "error">("reviewing");
    const [review, setReview] = useState<ReviewType & { submission: string }>();
    const [currentAnnotation, setCurrentAnnotation] = useState<Annotation | null>(null);
    const [clickToReveal, setCTR] = useState<boolean>(false);
    const interval = useRef<any>(null);

    const getReviewId = useCallback(async () => {
        try {
            const response = await api.get<ReviewType>(`/review/of?submission_id=${submissionId}`);
            if (!response.data)
                return setStatus("no_review");
            setReviewId(response.data.id);
            setStatus("reviewing");
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                navigator("/");
            } else
                setStatus("error");
        }
    }, [submissionId, navigator]);
    useEffect(() => void getReviewId(), [getReviewId]);

    const getSubmission = useCallback(async () => {
        try {
            const response = await api.get<Submission>(`/submission?id=${submissionId}`);
            return response.data;
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                navigator("/");
            } else
                setStatus("error");
        }
    }, [submissionId, navigator]);
    const getReview = useCallback(async () => {
        if (!reviewId) return;
        try {
            const response = await api.get<ReviewType>(`/review?id=${reviewId}`);
            if (response.data.status == "reviewing")
                return setStatus("reviewing");
            const submission = await getSubmission();
            setReview({
                ...response.data,
                submission: submission!.submission
            });
            setStatus('done');
            clearInterval(interval.current);
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                navigator("/");
            } else
                setStatus("error");
        }
    }, [reviewId, getSubmission, navigator]);
    useEffect(() => {
        if (!reviewId) return;
        getReview();
        interval.current = setInterval(() => void getReview(), 5000);
        return () => clearInterval(interval.current);
    }, [reviewId, getReview]);
    useEffect(() => {
        if (status == "error" || status == "done" || status == "failed")
            clearInterval(interval.current);
    }, [status]);
    useEffect(() => {
        if (!review) return;
        // Trigger animation shortly after mount
        const timer = setTimeout(() => setMounted(true), 100);
        return () => clearTimeout(timer);
    }, [review]);

    const reviewNow = useCallback(async () => {
        try {
            const response = await api.post<string>(`/review?submission_id=${submissionId}`);
            setStatus("reviewing");
            setReviewId(response.data);
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                navigator("/");
            } else
                setStatus("error");
        }
    }, [submissionId, navigator]);

    const annotations = useMemo<Annotation[]>(() => {
        if (!review) return [];
        if (!review.annotations) return [];
        if (!review.annotations.length) return [{ key: "0", text: review.submission, isAnnotation: false }];
        const annotations: Annotation[] = [];
        let lastIndex = 0;
        const submission = review.submission;
        for (const annotation of review.annotations) {
            const uniqueSearchPhrase = `${annotation.context_before} ${annotation.target_text}`;
            // Find the index in the real string
            const matchIndex = review.submission.indexOf(uniqueSearchPhrase);
            if (matchIndex == -1) continue;
            // The actual start index of the error is the match index + context length + 1 (for space)
            const startIndex = matchIndex + annotation.context_before.length + 1;
            const endIndex = startIndex + annotation.target_text.length;

            if (lastIndex < startIndex)
                annotations.push({
                    key: `${lastIndex}-${startIndex}`,
                    text: submission.slice(lastIndex, startIndex),
                    isAnnotation: false
                });
            annotations.push({
                key: `${startIndex}-${endIndex}`,
                text: submission.slice(startIndex, endIndex),
                isAnnotation: true,
                color: annotation.type == "grammar" ? "bg-amber-200/50"
                    : annotation.type == "coherence" ? "bg-blue-200/50"
                        : annotation.type == "mechanics" ? "bg-red-200/50"
                            : "bg-green-200/50",
                ...annotation
            });
            lastIndex = endIndex;
        }
        if (lastIndex < review.submission.length - 1)
            annotations.push({
                key: `${lastIndex}-${review.submission.length - 1}`,
                text: submission.slice(lastIndex, review.submission.length - 1),
                isAnnotation: false
            });
        return annotations;
    }, [review]);

    return <div className="w-full flex flex-1 min-h-0 overflow-auto">{
        status != "done" ? (
            status == "reviewing" ? <div className="m-auto flex flex-col items-center gap-5">
                <div className="relative">
                    <div className="absolute inset-0 bg-blue-100 rounded-full animate-ping opacity-75"></div>
                    <div className="relative bg-white p-6 rounded-full shadow-lg border ">
                        <Sparkle className="w-10 h-10 text-blue-500 animate-pulse" />
                    </div>
                </div>
                <div className="flex flex-col items-center">
                    <h1 className="text-3xl font-bold">Reviewing</h1>
                    <p className="text-xl px-10 text-center lg:p-0">The AI is reviewing your submission based on TOEIC standards</p>
                </div>
                <BarLoader width={300} />
            </div>
                : status == "failed"
                    ? <div className="m-auto flex flex-col items-center gap-5">
                        <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                            <Sparkle className="w-10 h-10 text-red-500 animate-pulse" />
                        </div>
                        <div className="flex flex-col items-center">
                            <h1 className="text-3xl font-bold">Failed to review</h1>
                            <p className="text-xl px-10 text-center lg:p-0">AI is failed to make a review</p>
                            <p className="text-xl px-10 text-center lg:p-0">Please submit the essay again</p>
                        </div>
                    </div>
                    : status == "error"
                        ? <div className="m-auto flex flex-col items-center gap-5">
                            <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                                <Bug className="w-10 h-10 text-red-500 animate-pulse" />
                            </div>
                            <div className="flex flex-col items-center">
                                <h1 className="text-3xl font-bold">Failed to get review</h1>
                                <p className="text-xl px-10 text-center lg:p-0">There is an error occured while fetching review</p>
                                <p className="text-xl text-center lg:p-0">Please look at the console or reload page</p>
                            </div>
                        </div>
                        : <div className="m-auto flex flex-col items-center gap-5">
                            <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                                <CircleQuestionMark className="w-10 h-10 text-red-500 animate-pulse" />
                            </div>
                            <div className="flex flex-col items-center">
                                <h1 className="text-3xl font-bold">No review</h1>
                                <p className="text-xl">This essay haven't been reviewed yet</p>
                                <div
                                    className="rounded-md p-3 mt-2 bg-slate-200 font-semibold cursor-pointer"
                                    onClick={() => reviewNow()}
                                >Review now</div>
                            </div>
                        </div>
        ) : !review
            ? <div className="m-auto flex flex-col items-center gap-5">
                <h1 className="text-3xl font-bold">Loading review</h1>
                <BarLoader width={300} />
            </div>
            : <div className="lg:mx-auto lg:py-10 w-full lg:w-4/5 h-full flex flex-col gap-5">
                <div
                    className="w-fit flex px-3 pt-5 lg:p-0 flex-row items-center text-slate-400 hover:text-slate-800 cursor-pointer transition-all duration-200"
                    onClick={() => navigator(`/topic/${review.topic_id}`, { viewTransition: true })}
                >
                    <ChevronLeft className="size-7" />
                    <p className="text-lg">Go back to topic</p>
                </div>
                <div className="flex flex-col lg:flex-row gap-10 lg:gap-5 lg:border-2 rounded-md p-5 h-fit">
                    <div className="flex flex-col flex-1 items-center lg:p-5">
                        <div className="relative flex items-center justify-center w-48 h-48 lg:mb-3">
                            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
                                {/* Background Circle */}
                                <circle
                                    cx="60"
                                    cy="60"
                                    r={radius}
                                    stroke="currentColor"
                                    strokeWidth="10"
                                    fill="transparent"
                                    strokeDasharray={radius * 2 * Math.PI}
                                    strokeDashoffset={mounted ? 0 : radius * 2 * Math.PI}
                                    strokeLinecap="round"
                                    className="text-indigo-100 transition-all duration-1500 ease-in-out"
                                />
                                {/* Progress Circle */}
                                <circle
                                    cx="60"
                                    cy="60"
                                    r={radius}
                                    stroke="currentColor"
                                    strokeWidth="10"
                                    fill="transparent"
                                    strokeDasharray={radius * 2 * Math.PI}
                                    strokeDashoffset={mounted ? radius * 2 * Math.PI * (1 - (review.score_range![1] + review.score_range![0]) / 2 / 200) : radius * 2 * Math.PI}
                                    strokeLinecap="round"
                                    className="text-indigo-600 transition-all duration-1750 ease-in-out"
                                />
                            </svg>
                            <div className="absolute flex flex-col items-center justify-center">
                                <p className="text-xl font-bold text-indigo-700">{review.score_range![0]} - {review.score_range![1]}</p>
                            </div>
                        </div>
                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Score range</h1>
                    </div>
                    <div className="flex flex-2 gap-3 flex-col">
                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Details</h1>
                        <div className="w-full flex flex-col gap-5">{
                            [
                                { title: "Grammar", score: review.detail_score!.grammar, icon: PenTool, bg: "bg-red-500" },
                                { title: "Vocabulary", score: review.detail_score!.vocabulary, icon: BookOpen, bg: "bg-blue-400" },
                                { title: "Organization", score: review.detail_score!.organization, icon: MessageSquare, bg: "bg-amber-500" },
                                { title: "Task fulfillment", score: review.detail_score!.task_fulfillment, icon: Percent, bg: "bg-slate-600" },
                            ].map(val => <div className="flex flex-col w-full gap-2">
                                <h2 className="text-xl flex flex-row items-center gap-2"><val.icon /> <span className="font-semibold">{val.title}</span> {val.score}</h2>
                                <div className="w-full h-2 rounded-full bg-slate-200">
                                    <div
                                        className={`h-2 rounded-full ${val.bg} transition-all ease-in-out duration-1000`}
                                        style={{
                                            width: mounted ? `${val.score}%` : '0%'
                                        }}
                                    />
                                </div>
                            </div>)
                        }</div>
                    </div>
                    <div className="flex-3 flex flex-col gap-2">
                        <h1 className="flex flex-row items-center gap-2 font-bold text-2xl text-slate-700 uppercase">
                            <Sparkles />
                            AI Feedback
                        </h1>
                        <p className={(mounted ? "opacity-100" : "opacity-0") + " text-lg overflow-y-auto transition-all duration-2000"}>{review.overall_feedback}</p>
                    </div>
                </div>
                {clickToReveal && currentAnnotation && currentAnnotation.isAnnotation &&
                    <div className="px-5 lg:p-5 lg:border-2 rounded-md h-fit text-xl">
                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Annotation</h1>
                        <p className="text-green-500">{currentAnnotation.replacement}</p>
                        <div className="w-full border-t-2" />
                        <p><span className="font-bold">Type:</span> {currentAnnotation.type}</p>
                        <p><span className="font-bold">Feedback:</span> {currentAnnotation.feedback}</p>
                    </div>
                }
                <div className="p-5 lg:border-2 rounded-md h-fit text-xl">
                    <div className="flex flex-row items-center">
                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Correction</h1>
                        <label className="flex flex-row items-center ml-auto gap-2">
                            <Checkbox
                                className="size-5"
                                checked={clickToReveal}
                                onCheckedChange={(checked) => { setCTR(!!checked); setCurrentAnnotation(null); }}
                            />
                            Click to reveal
                        </label>
                    </div>
                    <p>{annotations.map((annotation) => annotation.isAnnotation
                        ? clickToReveal
                            ? <span
                                key={annotation.key}
                                className={cn(
                                    mounted ? annotation.color : "",
                                    "whitespace-pre-wrap transition-all ease-in-out duration-500"
                                )}
                                onClick={() => setCurrentAnnotation(annotation)}
                            >{annotation.text}</span>
                            : <HoverCard>
                                <HoverCardTrigger asChild><span
                                    key={annotation.key}
                                    className={cn(
                                        mounted ? annotation.color : "",
                                        "whitespace-pre-wrap transition-all ease-in-out duration-500"
                                    )}
                            >{annotation.text}</span></HoverCardTrigger>
                            <HoverCardContent className="w-80">
                                <p className="text-green-500">{annotation.replacement}</p>
                                <div className="w-full border-t-2" />
                                <p><span className="font-bold">Type:</span> {annotation.type}</p>
                                <p><span className="font-bold">Feedback:</span> {annotation.feedback}</p>
                            </HoverCardContent>
                        </HoverCard>
                        : <span key={annotation.key} className=" whitespace-pre-wrap">{annotation.text}</span>
                    )}</p>
                </div>
                {review.improvement_suggestions && review.improvement_suggestions.length &&
                    <div className="px-5 lg:py-5 lg:border-2 rounded-md h-fit text-xl">
                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Sugesstions</h1>
                        <ul className="px-10 list-disc">
                            {review.improvement_suggestions?.map(val => <li>{val}</li>)}
                        </ul>
                    </div>
                }
            </div>
    }</div>;
}

export default Review;