import { useCallback, useEffect, useState } from "react";
import type { Statistics } from "@/lib/typing";
import api from "@/lib/api";
import { Skeleton } from "../ui/skeleton";
import ms from "ms";
import { ChartNoAxesCombined, Clock, FileText, Percent } from "lucide-react";
import { cn } from "@/lib/utils";

function Statics() {
    const [statistics, setStatistics] = useState<Statistics>();

    const getStatistics = useCallback(async () => {
        try {
            const response = await api.get<Statistics>("/statistics/");
            setStatistics(response.data);
        } catch (error) {
            console.error(error);
        }
    }, []);

    useEffect(() => void getStatistics(), [getStatistics]);

    return <div className="h-fit lg:h-35 py-5 px-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">{
        statistics
            ? <>
                {[
                    { label: 'Essays written', value: statistics.total_submission, icon: FileText },
                    { label: 'Average score', value: `${statistics.average_score.toFixed(0)}`, icon: ChartNoAxesCombined },
                    { label: 'Improvement rate', value: `+${(statistics.improvement_rate * 100).toFixed(1)}%`, icon: Percent, hiddenOnMobile: true },
                    { label: 'Total time', value: `${ms(statistics.total_time)}`, icon: Clock, hiddenOnMobile: true },
                ].map((stat, idx) => (
                    <div key={idx} className={cn(
                        "bg-white p-4 rounded-lg border-2 border-slate-200 flex items-center justify-between shadow-sm",
                        stat.hiddenOnMobile == true ? "hidden lg:flex" : ""
                    )}>
                        <div>
                            <p className="text-md text-slate-500 font-semibold uppercase">{stat.label}</p>
                            <p className="text-2xl font-bold text-slate-800">{stat.value}</p>
                        </div>
                        <stat.icon className="size-10 text-slate-200" />
                    </div>
                ))}
            </>
            : <>
                <Skeleton className="h-full w-full" />
                <Skeleton className="h-full w-full" />
                <Skeleton className="h-full w-full hidden lg:flex" />
                <Skeleton className="h-full w-full hidden lg:flex" />
            </>
    }</div>;
}

export default Statics;