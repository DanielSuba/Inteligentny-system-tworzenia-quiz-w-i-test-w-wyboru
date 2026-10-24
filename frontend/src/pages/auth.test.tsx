import { fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { mockFetch, renderPage, testUser } from "@/test/render";
import { setLocale } from "@/lib/locale";

function type(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}

describe("LoginPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setLocale("pl");
  });

  it("sprawdza pola przed wyslaniem", async () => {
    const fetchFn = mockFetch(200, {});
    renderPage(<LoginPage />);
    fireEvent.click(screen.getByRole("button", { name: "Zaloguj się" }));
    expect(await screen.findAllByText("To pole jest wymagane.")).toHaveLength(2);
    expect(fetchFn).not.toHaveBeenCalled();
  });

  it("pokazuje blad zlego hasla", async () => {
    mockFetch(401, { detail: "invalid_credentials" });
    document.cookie = "qf_csrf=abc";
    renderPage(<LoginPage />);
    type("E-mail", "ania@example.com");
    type("Hasło", "zle-haslo-123");
    fireEvent.click(screen.getByRole("button", { name: "Zaloguj się" }));
    expect(await screen.findByText("Nieprawidłowy e-mail lub hasło.")).toBeInTheDocument();
  });

  it("po zalogowaniu ustawia uzytkownika", async () => {
    mockFetch(200, testUser);
    document.cookie = "qf_csrf=abc";
    const auth = renderPage(<LoginPage />);
    type("E-mail", "ania@example.com");
    type("Hasło", "dobre-haslo-123");
    fireEvent.click(screen.getByRole("button", { name: "Zaloguj się" }));
    await vi.waitFor(() => expect(auth.setUser).toHaveBeenCalledWith(testUser));
  });

  it("dziala po angielsku", async () => {
    setLocale("en");
    mockFetch(200, {});
    renderPage(<LoginPage />);
    expect(screen.getByRole("heading", { name: "Log in" })).toBeInTheDocument();
  });
});

describe("RegisterPage", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("wymaga zgodnych hasel i poprawnej nazwy", async () => {
    const fetchFn = mockFetch(201, { status: "check_email" });
    renderPage(<RegisterPage />);
    type("E-mail", "ania@example.com");
    type("Nazwa użytkownika", "a b");
    type("Hasło", "dobre-haslo-123");
    type("Powtórz hasło", "inne-haslo-123");
    fireEvent.click(screen.getByRole("button", { name: "Załóż konto" }));
    expect(await screen.findByText("Hasła się różnią.")).toBeInTheDocument();
    expect(screen.getByText("Użyj 3–24 znaków: liter, cyfr lub _.")).toBeInTheDocument();
    expect(fetchFn).not.toHaveBeenCalled();
  });

  it("po rejestracji prosi o sprawdzenie skrzynki", async () => {
    mockFetch(201, { status: "check_email" });
    document.cookie = "qf_csrf=abc";
    renderPage(<RegisterPage />);
    type("E-mail", "ania@example.com");
    type("Nazwa użytkownika", "ania");
    type("Hasło", "dobre-haslo-123");
    type("Powtórz hasło", "dobre-haslo-123");
    fireEvent.click(screen.getByRole("button", { name: "Załóż konto" }));
    expect(await screen.findByText(/Wysłaliśmy link na ania@example.com/)).toBeInTheDocument();
  });
});
