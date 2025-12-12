import { useCallback, useEffect, useState } from "react";
import type { Statistics } from "@/lib/typing";
import api from "@/lib/api";
import { Skeleton } from "../ui/skeleton";
import ms from "ms";
import { ChartNoAxesCombined, Clock, FileText, Percent } from "lucide-react";

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

    return <div className="h-35 py-5 px-10 grid grid-cols-4 grid-rows-1 gap-5">{
        statistics
            ? <>
                {[
                    { label: 'Essays written', value: statistics.total_submission, icon: FileText },
                    { label: 'Average score', value: `${statistics.average_score.toFixed(0)}`, icon: ChartNoAxesCombined },
                    { label: 'Improvement rate', value: `+${(statistics.improvement_rate * 100).toFixed(1)}%`, icon: Percent },
                    { label: 'Total time', value: `${ms(statistics.total_time)}`, icon: Clock },
                ].map((stat, idx) => (
                    <div key={idx} className="bg-white p-4 rounded-lg border-2 border-slate-200 flex items-center justify-between shadow-sm">
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
                <Skeleton className="h-full w-full" />
                <Skeleton className="h-full w-full" />
            </>
    }</div>;
}

export default Statics;