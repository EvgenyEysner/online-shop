import { Suspense } from "react";
import { ShopPageClient } from "@/src/components/ShopPageClient";

export default function HomePage() {
    return (
        <Suspense fallback={<div className="flex-1" />}>
            <ShopPageClient />
        </Suspense>
    );
}