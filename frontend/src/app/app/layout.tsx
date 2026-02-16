"use client";

import NavBar from "@/src/components/layout/NavBar";
import { Sidebar } from "@/src/components/layout/Sidebar";
import { getProtectedRedirect } from "@/src/router/redirects";
import { useAuthStore } from "@/src/store/useAuthStore";
import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";


export default function Layout({ children }: { children: ReactNode }) {

    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
    const router = useRouter();
    const bootstrapSession = useAuthStore((state) => state.bootstrapSession);
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const isBootstrapped = useAuthStore((state) => state.isBootstrapped);

    useEffect(() => {
        void bootstrapSession();
    }, [bootstrapSession]);

    useEffect(() => {
        const redirectPath = isBootstrapped ? getProtectedRedirect(isAuthenticated) : null;

        if (redirectPath) {
            router.replace(redirectPath);
        }
    }, [isAuthenticated, isBootstrapped, router]);

    if (!isBootstrapped || !isAuthenticated) {
        return null;
    }

    return (
        <div className="min-h-screen">
            <NavBar onOpenMenu={() => setMobileMenuOpen((prev) => !prev)} />

            <div className="relative flex w-full">
                <Sidebar mobileOpen={mobileMenuOpen} closeMobile={() => setMobileMenuOpen(false)} />
                <main className="w-full min-w-0 flex justify-center items-center">
                    {children}
                </main>
            </div>
        </div>
    );
}
