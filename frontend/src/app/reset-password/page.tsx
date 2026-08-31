"use client";

import {FormEvent, Suspense, useState} from "react";
import {useRouter, useSearchParams} from "next/navigation";
import {Loader2, Sun} from "lucide-react";
import {ApiError} from "@/src/lib/api";
import {confirmPasswordReset} from "@/src/lib/auth";
import {useApp} from "@/src/providers/AppProvider";

function ResetPasswordContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const {openLogin} = useApp();

    const uid = searchParams.get("uid") ?? "";
    const token = searchParams.get("token") ?? "";
    const missingParams = !uid || !token;

    const [password, setPassword] = useState("");
    const [passwordConfirm, setPasswordConfirm] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [errors, setErrors] = useState<string[]>([]);

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();
        setErrors([]);
        setIsSubmitting(true);

        try {
            await confirmPasswordReset(uid, token, password, passwordConfirm);
            setSuccess(true);
        } catch (err) {
            const messages =
                err instanceof ApiError
                    ? [...err.generalErrors, ...Object.values(err.fieldErrors).flat()]
                    : [];
            setErrors(
                messages.length > 0
                    ? messages
                    : [
                        "Der Link ist ungültig oder abgelaufen. Bitte fordern Sie einen neuen Link an.",
                    ]
            );
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleGoToLogin = () => {
        router.push("/");
        openLogin();
    };

    return (
        <div className="max-w-md mx-auto px-4 py-16">
            <div className="bg-card border border-border rounded-2xl shadow-2xl p-6 space-y-4">
                <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded bg-primary flex items-center justify-center">
                        <Sun size={15} className="text-accent"/>
                    </div>
                    <div>
                        <div
                            className="text-foreground font-bold leading-none"
                            style={{fontFamily: "var(--font-display)", fontSize: "0.95rem"}}
                        >
                            KÖNIG<span className="text-accent">39</span>
                        </div>
                        <div className="text-muted-foreground leading-none" style={{fontSize: "0.6rem"}}>
                            Passwort zurücksetzen
                        </div>
                    </div>
                </div>

                {missingParams ? (
                    <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-xs text-destructive">
                        Der Link ist unvollständig. Bitte fordern Sie über &bdquo;Passwort
                        vergessen?&ldquo; in der Anmeldung einen neuen Link an.
                    </div>
                ) : success ? (
                    <>
                        <div className="p-3 bg-primary/10 border border-primary/30 rounded-lg text-xs text-foreground">
                            Ihr Passwort wurde erfolgreich geändert. Sie können sich jetzt
                            anmelden.
                        </div>
                        <button
                            type="button"
                            onClick={handleGoToLogin}
                            className="w-full py-3 bg-primary text-primary-foreground font-bold rounded-lg hover:bg-primary/90 transition-colors"
                            style={{fontFamily: "var(--font-display)"}}
                        >
                            Zur Anmeldung
                        </button>
                    </>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label
                                htmlFor="new-password"
                                className="text-foreground text-sm font-semibold block mb-1.5"
                            >
                                Neues Passwort
                            </label>
                            <input
                                id="new-password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                autoComplete="new-password"
                                disabled={isSubmitting}
                                className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-60"
                            />
                        </div>
                        <div>
                            <label
                                htmlFor="new-password-confirm"
                                className="text-foreground text-sm font-semibold block mb-1.5"
                            >
                                Neues Passwort bestätigen
                            </label>
                            <input
                                id="new-password-confirm"
                                type="password"
                                value={passwordConfirm}
                                onChange={(e) => setPasswordConfirm(e.target.value)}
                                required
                                autoComplete="new-password"
                                disabled={isSubmitting}
                                className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-60"
                            />
                        </div>

                        {errors.length > 0 && (
                            <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-xs text-destructive">
                                {errors.length === 1 ? (
                                    <p>{errors[0]}</p>
                                ) : (
                                    <ul className="list-disc pl-4 space-y-1">
                                        {errors.map((message, index) => (
                                            <li key={`${message}-${index}`}>{message}</li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full py-3 bg-primary text-primary-foreground font-bold rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
                            style={{fontFamily: "var(--font-display)"}}
                        >
                            {isSubmitting ? (
                                <>
                                    <Loader2 size={16} className="animate-spin"/>
                                    Wird gespeichert…
                                </>
                            ) : (
                                "Passwort setzen"
                            )}
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}

export default function ResetPasswordPage() {
    return (
        <Suspense
            fallback={
                <div className="flex-1 py-16 text-center text-sm text-muted-foreground">
                    Wird geladen…
                </div>
            }
        >
            <ResetPasswordContent/>
        </Suspense>
    );
}
