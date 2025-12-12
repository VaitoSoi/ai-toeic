import Header from "@/components/Header";
import Detail from "@/components/Topic/Detail";
import Generate from "@/components/Topic/Generate";
import Review from "@/components/Topic/Review";
import Submit from "@/components/Topic/Submit";
import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router";

function Topic() {
    const location = useLocation();
    const navigator = useNavigate();
    const [, parent, id1, child, id2] = location.pathname.split("/");

    useEffect(() => parent != "topic" ? void navigator("/") : undefined, [parent, navigator]);

    return <div className="w-screen h-screen flex flex-col">
        <Header />
        {
            id1 == "new"
                ? <Generate />
                : child == "submit"
                    ? <Submit topicId={id1} preloadedData={location.state ? JSON.parse(location.state) : undefined} />
                    : child == "submission"
                        ? <Review submissionId={id2} />
                        : <Detail topicId={id1} preloadedData={location.state ? JSON.parse(location.state) : undefined} />
        }
    </div>;
}

export default Topic;