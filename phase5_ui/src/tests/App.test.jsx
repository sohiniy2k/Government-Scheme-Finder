import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "../App";

const mockMeta = {
  states: [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
  ],
  occupations: ["student", "farmer", "fisherman", "artisan", "construction_worker", "entrepreneur", "unemployed", "senior_citizen", "other"],
  genders: ["male", "female", "transgender", "prefer_not_to_say"],
  social_categories: ["General", "SC", "ST", "OBC", "EWS", "Minority", "prefer_not_to_say"],
  bpl: ["yes", "no", "unknown"],
  interests: [
    "Agriculture", "Banking", "Business & Entrepreneurship", "Education & Learning",
    "Financial Services and Insurance", "Health & Wellness", "Housing & Shelter",
    "IT & Communications", "Law & Justice", "Public Safety", "Rural & Environment",
    "Science", "Skills & Employment", "Social welfare & Empowerment", "Sports & Culture",
    "Transport & Infrastructure", "Travel & Tourism", "Utility & Sanitation", "Women and Child"
  ],
  languages: ["en", "hi"],
};

describe("Phase 5 UI Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // =====================================================================
  // 1. Dropdowns Populate From /api/meta
  // =====================================================================
  it("populates dropdowns from /api/meta", async () => {
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.includes("/api/meta")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockMeta),
        });
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(<App />);

    // Verify all 36 states are loaded into state dropdown
    await waitFor(() => {
      const stateSelect = screen.getByLabelText(/state \/ union territory/i);
      expect(stateSelect).toBeInTheDocument();
      // Total options = 1 default placeholder + 36 states = 37
      expect(stateSelect.querySelectorAll("option").length).toBe(37);
      expect(screen.getByText("Maharashtra")).toBeInTheDocument();
      expect(screen.getByText("Goa")).toBeInTheDocument();
    });

    // Verify occupations dropdown
    const occupationSelect = screen.getByLabelText(/occupation/i);
    expect(occupationSelect.querySelectorAll("option").length).toBe(mockMeta.occupations.length);

    // Verify 19 interest chips are displayed
    await waitFor(() => {
      expect(screen.getByText(/Agriculture/i)).toBeInTheDocument();
      expect(screen.getByText(/Education & Learning/i)).toBeInTheDocument();
    });
  });

  // =====================================================================
  // 2. Validation Blocks Empty Age / State
  // =====================================================================
  it("blocks submission and shows validation errors when age or state is empty", async () => {
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.includes("/api/meta")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockMeta),
        });
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Maharashtra")).toBeInTheDocument();
    });

    const submitBtn = screen.getByRole("button", { name: /find schemes/i });
    fireEvent.click(submitBtn);

    // Expect validation errors to appear
    await waitFor(() => {
      expect(screen.getByText(/age \(years\) is required/i)).toBeInTheDocument();
      expect(screen.getByText(/state \/ union territory is required/i)).toBeInTheDocument();
    });

    // Ensure POST /api/recommend was NOT called
    expect(global.fetch).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/recommend"),
      expect.anything()
    );
  });

  // =====================================================================
  // 3. Results Render Cards
  // =====================================================================
  it("renders scheme cards and more schemes on successful recommendation", async () => {
    const mockRecommendResponse = {
      count: 1,
      language: "en",
      results: [
        {
          id: "pm-kisan",
          name: "Pradhan Mantri Kisan Samman Nidhi",
          level: "central",
          benefits: "Income support of Rs 6,000 per year in three equal installments",
          summary: "Direct income support for farmers.",
          why_you_qualify: "You are a registered farmer in Maharashtra.",
          things_to_check: ["Confirm land records are updated"],
          documents_needed: ["Aadhaar card", "Land records", "Bank account details"],
          how_to_apply: ["Step 1: Visit PM-Kisan portal", "Step 2: Submit Aadhaar details"],
          official_url: "https://www.myscheme.gov.in/schemes/pm-kisan",
          score: 10,
          source: "llm",
        },
      ],
      more_schemes: [
        {
          id: "more-scheme-1",
          name: "Maharashtra Agro Subsidy",
          level: "state",
          benefits: "Financial aid for drip irrigation",
          official_url: "https://mahadbt.maharashtra.gov.in",
        },
      ],
      relaxation_hint: null,
      disclaimer: "Guidance only.",
    };

    global.fetch = vi.fn().mockImplementation((url, opts) => {
      if (url.includes("/api/meta")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockMeta),
        });
      }
      if (url.includes("/api/recommend") && opts?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockRecommendResponse),
        });
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByLabelText(/state \/ union territory/i)).toBeInTheDocument();
    });

    // Fill valid age and state
    const ageInput = screen.getByPlaceholderText(/e\.g\. 25/i);
    fireEvent.change(ageInput, { target: { value: "30" } });

    const stateSelect = screen.getByLabelText(/state \/ union territory/i);
    fireEvent.change(stateSelect, { target: { value: "Maharashtra" } });

    // Submit form
    const submitBtn = screen.getByRole("button", { name: /find schemes/i });
    fireEvent.click(submitBtn);

    // Verify card content renders
    await waitFor(() => {
      expect(screen.getByText("Pradhan Mantri Kisan Samman Nidhi")).toBeInTheDocument();
      expect(screen.getByText(/Income support of Rs 6,000 per year/i)).toBeInTheDocument();
      expect(screen.getByText("You are a registered farmer in Maharashtra.")).toBeInTheDocument();
      expect(screen.getByText("Aadhaar card")).toBeInTheDocument();
      expect(screen.getByText("Land records")).toBeInTheDocument();
      expect(screen.getByText("Step 1: Visit PM-Kisan portal")).toBeInTheDocument();
      expect(screen.getByText("AI Explained")).toBeInTheDocument();
    });

    // Verify more schemes section renders
    expect(screen.getByText("Maharashtra Agro Subsidy")).toBeInTheDocument();
  });

  // =====================================================================
  // 4. Empty State Shows Relaxation Hint
  // =====================================================================
  it("displays empty state with relaxation hint when zero schemes match", async () => {
    const mockEmptyResponse = {
      count: 0,
      language: "en",
      results: [],
      more_schemes: [],
      relaxation_hint: "4 schemes match if you ignore the income limit",
      disclaimer: "Official guidance only.",
    };

    global.fetch = vi.fn().mockImplementation((url, opts) => {
      if (url.includes("/api/meta")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockMeta),
        });
      }
      if (url.includes("/api/recommend") && opts?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockEmptyResponse),
        });
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByLabelText(/state \/ union territory/i)).toBeInTheDocument();
    });

    // Fill in age and state
    const ageInput = screen.getByPlaceholderText(/e\.g\. 25/i);
    fireEvent.change(ageInput, { target: { value: "45" } });

    const stateSelect = screen.getByLabelText(/state \/ union territory/i);
    fireEvent.change(stateSelect, { target: { value: "Goa" } });

    // Submit form
    const submitBtn = screen.getByRole("button", { name: /find schemes/i });
    fireEvent.click(submitBtn);

    // Verify empty state title and relaxation hint are visible
    await waitFor(() => {
      expect(screen.getByText("No Direct Matches Found")).toBeInTheDocument();
      expect(screen.getByText(/4 schemes match if you ignore the income limit/i)).toBeInTheDocument();
    });
  });
});
