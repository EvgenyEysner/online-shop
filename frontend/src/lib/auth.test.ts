import { afterEach, describe, expect, it, vi } from "vitest";
import { confirmPasswordReset, requestPasswordReset } from "@/src/lib/auth";

describe("password reset helpers", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("requestPasswordReset sendet die E-Mail an den Request-Endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await requestPasswordReset("reset@example.com");

    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/api/v1/accounts/password-reset/"
    );
    expect(JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body))).toEqual({
      email: "reset@example.com",
    });
  });

  it("confirmPasswordReset sendet uid, token und beide Passwörter", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await confirmPasswordReset("uid", "token", "NewSecurePass123!", "NewSecurePass123!");

    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/api/v1/accounts/password-reset/confirm/"
    );
    expect(JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body))).toEqual({
      uid: "uid",
      token: "token",
      password: "NewSecurePass123!",
      password_confirm: "NewSecurePass123!",
    });
  });
});
