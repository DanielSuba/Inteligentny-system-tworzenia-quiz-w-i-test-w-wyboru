import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { HealthPage } from "./HealthPage";

function mockFetch(body: object) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ json: () => Promise.resolve(body) }));
}

describe("HealthPage", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("pokazuje, ze wszystko dziala", async () => {
    mockFetch({ status: "ok", db: "ok", redis: "ok" });
    render(<HealthPage />);
    expect(await screen.findAllByText("działa")).toHaveLength(3);
  });

  it("pokazuje, ze baza nie odpowiada", async () => {
    mockFetch({ status: "error", db: "error", redis: "ok" });
    render(<HealthPage />);
    expect(await screen.findByText("nie odpowiada")).toBeInTheDocument();
    expect(screen.getAllByText("działa")).toHaveLength(2);
  });

  it("pokazuje, ze backend nie odpowiada", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("brak polaczenia")));
    render(<HealthPage />);
    expect(await screen.findAllByText("nie odpowiada")).toHaveLength(3);
  });
});
