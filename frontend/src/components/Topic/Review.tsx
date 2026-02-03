import { BookOpen, Bug, ChevronLeft, ChevronsLeftRightEllipsis, CircleQuestionMark, MessageSquare, PenTool, Percent, Sparkle, Sparkles } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ComponentProps } from "react";
import { BarLoader } from "react-spinners";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "../ui/hover-card";
import { apiGetReview, apiGetReviewOfSubmission, apiGetSubmission, apiGetTopic, apiRequestReview, type SlicedSubmission, type Annotation as ReviewAnnotation, type SlicedReview, type SlicedTopic, apiDeleteReview } from "@/api";
import axios from "axios";
import { error, success } from "../Toast";
import { useNavigate } from "react-router";
import { cn } from "@/lib/utils";
import { Checkbox } from "../ui/checkbox";
import { BACKEND_URL } from "@/api/client.gen";

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
    const routerNavigator = useNavigate();

    const [mounted, setMounted] = useState(false);

    const [reviewId, setReviewId] = useState<string>();
    const [status, setStatus] = useState<"no_review" | "reviewing" | "failed" | "done" | "error" | "service_failure">("reviewing");
    const [topic, setTopic] = useState<SlicedTopic>();
    const [submission, setSubmission] = useState<SlicedSubmission>();
    const [review, setReview] = useState<SlicedReview>();
    const interval = useRef<any>(null);

    const [currentAnnotation, setCurrentAnnotation] = useState<Annotation | null>(null);
    const [clickToReveal, setCTR] = useState<boolean>(false);

    const getReviewId = useCallback(async () => {
        try {
            const response = await apiGetReviewOfSubmission({ query: { submission_id: submissionId } });
            if (!response.data || !response.data!.id)
                return setStatus("no_review");
            setReviewId(response.data.id);
            setStatus("reviewing");
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                routerNavigator("/");
            } else
                setStatus("error");
        }
    }, [submissionId, routerNavigator]);
    useEffect(() => void getReviewId(), [getReviewId]);

    const getSubmission = useCallback(async () => {
        try {
            const response = await apiGetSubmission({ query: { id: submissionId } });
            if (!response.data) return setStatus("error");
            setSubmission(response.data);
            return response.data;
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                routerNavigator("/");
            } else
                setStatus("error");
        }
    }, [submissionId, routerNavigator]);
    const getTopic = useCallback(async () => {
        if (!review) return;
        try {
            const response = await apiGetTopic({ query: { id: review!.topic_id } });
            if (!response.data) return setStatus("error");
            setTopic(response.data);
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                routerNavigator("/");
            } else
                setStatus("error");
        }
    }, [review, routerNavigator]);
    const getReview = useCallback(async () => {
        if (!reviewId) return;
        try {
            const response = await apiGetReview({ query: { id: reviewId } });
            if (!response.data) return setStatus("error");
            if (response.data.status == "pending")
                return setStatus("reviewing");
            if (response.data.status == "failed")
                return setStatus("failed");
            if (response.data.status == "service_failed")
                return setStatus("service_failure");
            if (!response.data.overall)
                return setStatus("error");
            setReview(response.data);
            setStatus('done');
            clearInterval(interval.current);
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                routerNavigator("/");
            } else
                setStatus("error");
        }
    }, [reviewId, routerNavigator]);

    useEffect(() => {
        if (!reviewId) return;
        getReview();
        interval.current = setInterval(() => void getReview(), 5000);
        return () => clearInterval(interval.current);
    }, [reviewId, getReview]);

    useEffect(() => {
        if (status === 'done' && review && !topic) {
            getTopic();
        }
    }, [status, review, topic, getTopic]);
    useEffect(() => {
        if (status === 'done' && !submission) {
            getSubmission();
        }
    }, [status, submission, getSubmission]);
    useEffect(() => {
        if (status == "error" || status == "done" || status == "failed")
            clearInterval(interval.current);
    }, [status]);
    useEffect(() => {
        if (!review) return;
        const timer = setTimeout(() => setMounted(true), 100); // The appear effect :D
        return () => clearTimeout(timer);
    }, [review]);

    const reviewNow = useCallback(async () => {
        try {
            const response = await apiRequestReview({ query: { submission_id: submissionId } });
            if (!response.data || !Object.keys(response.data).length)
                return error("Can't request a review");
            setStatus("reviewing");
            setReviewId(response.data);
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                routerNavigator("/");
            } else
                setStatus("error");
        }
    }, [submissionId, routerNavigator]);

    const reReview = useCallback(async () => {
        if (!reviewId) return error("Can't find review id D:");
        try {
            const deleteResponse = await apiDeleteReview({ query: { id: reviewId } });
            if (!deleteResponse.data || !Object.keys(deleteResponse.data).length)
                return error("Can't delete review");
            const reviewResponse = await apiRequestReview({ query: { submission_id: submissionId } });
            if (!reviewResponse.data || !reviewResponse.data.length)
                return error("Can't request a review");
            setReviewId(reviewResponse.data);
            setStatus("reviewing");
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.status == 404) {
                error("Submission or review not found");
                routerNavigator("/");
            } else
                setStatus("error");
        }
    }, [reviewId, submissionId, routerNavigator]);

    const pasteSubmission = useCallback(async () => {
        const submissionObj = submission || await getSubmission();
        if (!submissionObj) return error("Can't get submission");
        navigator.clipboard.writeText(submissionObj.answers!.map(val => val.content).join("\n"));
        return success("Pasted :D");
    }, [submission, getSubmission]);


    const annotations = useCallback((submission: string, reviewAnnotations: ReviewAnnotation[]): Annotation[] => {
        if (!review || !reviewAnnotations || !reviewAnnotations.length) return [{ key: "0", text: submission, isAnnotation: false }];
        const annotations: Annotation[] = [];
        let lastIndex = 0;
        for (const annotation of reviewAnnotations) {
            // Find the index in the real string
            let uniqueSearchPhrase = annotation.target_text;
            let matchIndex = submission.indexOf(uniqueSearchPhrase, lastIndex);
            let startIndex = 0, endIndex = 0;

            if (matchIndex == -1) {
                uniqueSearchPhrase = annotation.context_before + " " + uniqueSearchPhrase;

                matchIndex = submission.indexOf(uniqueSearchPhrase, lastIndex);
                if (matchIndex == -1) {
                    console.log("can't find match of", annotation);
                    continue;
                } else {
                    startIndex = matchIndex + annotation.context_before.length + 1;
                    endIndex = startIndex + annotation.target_text.length;
                }
            } else {
                startIndex = matchIndex;
                endIndex = startIndex + annotation.target_text.length;
            }

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
        if (lastIndex < submission.length)
            annotations.push({
                key: `${lastIndex}-${submission.length}`,
                text: submission.slice(lastIndex),
                isAnnotation: false
            });
        return annotations;
    }, [review]);

    return <div className="w-full h-fit flex flex-1 min-h-0 overflow-auto">{
        status != "done" ? (
            status == "reviewing"
                ? <Container>
                    <div className="relative">
                        <div className="absolute inset-0 bg-blue-100 rounded-full animate-ping opacity-75"></div>
                        <div className="relative bg-white p-6 rounded-full shadow-lg border ">
                            <Sparkle className="w-10 h-10 text-blue-500 animate-pulse" />
                        </div>
                    </div>
                    <TextContainer>
                        <h1 className="text-3xl font-bold">Reviewing</h1>
                        <p className="text-xl px-10 text-center lg:p-0">The AI is reviewing your submission based on TOEIC standards</p>
                    </TextContainer>
                    <BarLoader width={300} />
                </Container>
                : status == "failed"
                    ? <Container>
                        <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                            <Sparkle className="w-10 h-10 text-red-500" />
                        </div>
                        <TextContainer>
                            <h1 className="text-3xl font-bold">Failed to review</h1>
                            <p className="text-xl px-10 text-center lg:p-0">AI is failed to make a review</p>
                            <p className="text-xl px-10 text-center lg:p-0">Please submit the essay again</p>
                        </TextContainer>
                        <RetryButtons reReview={reReview} pasteSubmission={pasteSubmission} />
                    </Container>
                    : status == "service_failure"
                        ? <Container>
                            <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                                <ChevronsLeftRightEllipsis className="w-10 h-10 text-red-500" />
                            </div>
                            <TextContainer>
                                <h1 className="text-3xl font-bold">Service Failure</h1>
                                <p className="text-xl text-center lg:p-0">
                                    The AI provider returns unexpected code (not 200 or not SUCCESS)<br />
                                    Please take a look at the server console and API console then try again later
                                </p>
                            </TextContainer>
                            <RetryButtons reReview={reReview} pasteSubmission={pasteSubmission} />
                        </Container>
                        : status == "error"
                            ? <Container>
                                <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                                    <Bug className="w-10 h-10 text-red-500" />
                                </div>
                                <TextContainer>
                                    <h1 className="text-3xl font-bold">Failed to get review</h1>
                                    <p className="text-xl px-10 text-center lg:p-0">There is an error occured while fetching review</p>
                                    <p className="text-xl text-center lg:p-0">Please look at the console or reload page</p>
                                </TextContainer>
                                <Button onClick={pasteSubmission}>Copy submission to clipboard</Button>
                            </Container>
                            : <Container>
                                <div className="bg-red-300 p-6 rounded-full shadow-lg border ">
                                    <CircleQuestionMark className="w-10 h-10 text-red-500" />
                                </div>
                                <TextContainer>
                                    <h1 className="text-3xl font-bold">No review</h1>
                                    <p className="text-xl">This essay haven't been reviewed yet</p>
                                    <Button onClick={() => reviewNow()}>Review now</Button>
                                </TextContainer>
                            </Container>
        ) : !review || !topic || !submission
            ? <Container>
                <h1 className="text-3xl font-bold">Loading data</h1>
                <BarLoader width={300} />
            </Container>
            : <div className="lg:mx-auto my-5 lg:my-10 w-full lg:w-4/5 h-fit flex flex-col gap-5">
                <div
                    className="w-fit flex px-3 lg:p-0 flex-row items-center text-slate-400 hover:text-slate-800 cursor-pointer transition-all duration-200"
                    onClick={() => routerNavigator(`/topic/${review.topic_id}`, { viewTransition: true })}
                >
                    <ChevronLeft className="size-7" />
                    <p className="text-lg">Go back to topic</p>
                </div>
                <div className="flex flex-col lg:py-5 lg:flex-row gap-5 lg:gap-5 lg:border-2 rounded-md px-5 h-fit">
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
                                    strokeDashoffset={mounted ? radius * 2 * Math.PI * (1 - (review.overall!.score_range![1] + review.overall!.score_range![0]) / 2 / 200) : radius * 2 * Math.PI}
                                    strokeLinecap="round"
                                    className="text-indigo-600 transition-all duration-1750 ease-in-out"
                                />
                            </svg>
                            <div className="absolute flex flex-col items-center justify-center">
                                <p className="text-xl font-bold text-indigo-700">{review.overall!.score_range![0]} - {review.overall!.score_range![1]}</p>
                            </div>
                        </div>
                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Score range</h1>
                    </div>
                    <div className="flex flex-2 gap-3 flex-col">
                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Details</h1>
                        <div className="w-full flex flex-col gap-5">{
                            [
                                { title: "Grammar", score: review.overall!.detail_score!.grammar, icon: PenTool, bg: "bg-red-500" },
                                { title: "Vocabulary", score: review.overall!.detail_score!.vocabulary, icon: BookOpen, bg: "bg-blue-400" },
                                { title: "Organization", score: review.overall!.detail_score!.organization, icon: MessageSquare, bg: "bg-amber-500" },
                                { title: "Task fulfillment", score: review.overall!.detail_score!.task_fulfillment, icon: Percent, bg: "bg-slate-600" },
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
                        <p className={(mounted ? "opacity-100" : "opacity-0") + " text-lg overflow-y-auto transition-all duration-2000"}>{review.overall!.overall_feedback}</p>
                    </div>
                </div>
                {clickToReveal && currentAnnotation && currentAnnotation.isAnnotation &&
                    <div className="px-5 lg:py-5 lg:border-2 rounded-md h-fit text-xl">
                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Annotation</h1>
                        <p className="text-green-500">{currentAnnotation.replacement}</p>
                        <div className="w-full border-t-2" />
                        <p><span className="font-bold">Type:</span> {currentAnnotation.type}</p>
                        <p><span className="font-bold">Feedback:</span> {currentAnnotation.feedback}</p>
                    </div>
                }
                <div className="px-5 lg:py-5 lg:border-2 rounded-md h-fit text-xl">
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
                    {topic?.part == "1"
                        ? <div className="size-full flex flex-col gap-5 pt-5 px-5">{
                            submission.answers!.map(val => {
                                const question = topic.questions!.find(quesionVal => quesionVal.id == val.question_id);
                                const answerReview = review.answers!.find(answerVal => answerVal.answer_id == val.id);
                                if (!question || !answerReview) return;
                                return <div className="flex flex-col xl:flex-row gap-10 items-center p-5 rounded-md border-2">
                                    <img
                                        className="h-1/5 xl:w-1/5 rounded-md"
                                        src={`${BACKEND_URL}/file/${question.file}`}
                                    />
                                    <div className="h-2/5 xl:w-2/5">
                                        <h2 className="font-bold text-xl text-slate-700 uppercase">Feedback</h2>
                                        <p>{answerReview.feedback}</p>
                                        <h2 className="font-bold text-xl text-slate-700 uppercase">Correction</h2>
                                        <UseAnnotation
                                            annotations={annotations(val.content, answerReview.annotations!)}
                                            clickToReveal={clickToReveal}
                                            mounted={mounted}
                                            setCurrentAnnotation={setCurrentAnnotation}
                                        />
                                    </div>
                                    <div className="h-2/5 w-full xl:w-2/5 flex flex-2 gap-3 flex-col">
                                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Details</h1>
                                        <div className="w-full flex flex-col gap-5">{
                                            [
                                                { title: "Grammar", score: answerReview.details.grammar, icon: PenTool, bg: "bg-red-500" },
                                                { title: "Visual Relevance", score: answerReview.details.visual_relevance, icon: BookOpen, bg: "bg-teal-400" },
                                            ].map(val => <div className="flex flex-col w-full gap-2">
                                                <h2 className="text-xl flex flex-row items-center gap-2"><val.icon /> <span className="font-semibold">{val.title}</span> {val.score}</h2>
                                                <div className="w-full h-2 rounded-full bg-slate-200">
                                                    <div
                                                        className={`h-2 rounded-full ${val.bg} transition-all ease-in-out duration-1000`}
                                                        style={{
                                                            width: mounted ? `${val.score * 10}%` : '0%'
                                                        }}
                                                    />
                                                </div>
                                            </div>)
                                        }</div>
                                    </div>
                                </div>;
                            })
                        }</div>
                        : <UseAnnotation
                            annotations={annotations(submission.answers![0].content, review.overall!.annotations!)}
                            clickToReveal={clickToReveal}
                            mounted={mounted}
                            setCurrentAnnotation={setCurrentAnnotation}
                        />
                    }
                </div>
                {review.overall!.improvement_suggestions && review.overall!.improvement_suggestions.length &&
                    <div className="px-5 lg:py-5 lg:border-2 rounded-md h-fit text-xl">
                        <h1 className="font-bold text-2xl text-slate-700 uppercase">Sugesstions</h1>
                        <ul className="px-10 list-disc">
                            {review.overall!.improvement_suggestions?.map(val => <li>{val}</li>)}
                        </ul>
                    </div>
                }
            </div>
    }</div>;
}

function UseAnnotation({
    annotations, clickToReveal, mounted, setCurrentAnnotation }:
    { annotations: Annotation[], clickToReveal: boolean, mounted: boolean, setCurrentAnnotation: (obj: any) => any }
) {
    return <p>{annotations.map((annotation) => annotation.isAnnotation
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
    )}</p>;
}

function Button({ className, ...prop }: ComponentProps<"div">) {
    return <div
        className={cn("rounded-md p-3 mt-2 xl:bg-slate-100 xl:hover:shadow-md xl:hover:bg-slate-200 bg-slate-200 transition-all duration-200 font-semibold cursor-pointer", className)}
        {...prop}
    />;
}

function RetryButtons({ reReview, pasteSubmission }: { reReview: () => any, pasteSubmission: () => any }) {
    return <div className="flex flex-col items-center md:flex-row gap-2">
        <Button onClick={() => reReview()}>Review again</Button>
        <Button onClick={() => pasteSubmission()}>Copy submission to clipboard</Button>
    </div>;
}

function Container({ className, ...prop }: ComponentProps<"div">) {
    return <div
        className={cn("m-auto flex flex-col items-center gap-5", className)}
        {...prop}
    />;
}


function TextContainer({ className, ...prop }: ComponentProps<"div">) {
    return <div
        className={cn("flex flex-col items-center", className)}
        {...prop}
    />;
}

export default Review;