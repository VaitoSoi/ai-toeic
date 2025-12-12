import Header from "@/components/Header";
import List from "@/components/Topics/List";
import Statics from "@/components/Topics/Statistics";

function Topics() {
    return <div className="h-screen w-screen flex flex-col overflow-auto">
        <Header />
        <Statics />
        <List />
    </div>;
}

export default Topics;