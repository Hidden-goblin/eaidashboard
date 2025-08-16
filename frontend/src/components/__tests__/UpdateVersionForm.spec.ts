import { render, screen, fireEvent, waitFor } from "@testing-library/vue";
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { createTestingPinia } from "@pinia/testing";
import UpdateVersionForm from "@/components/versions/UpdateVersionForm.vue";
import { server } from "@/mocks/node";
import { updateVersionHandlers } from "@/mocks/updateVersionHandlers";

// Mock composables
vi.mock("@/composables/useApiBaseUrl", () => ({
    useApiBaseUrl: () => "http://mock-api"
}));
vi.mock("@/stores/authStore", () => ({
    useAuthStore: () => ({
        token: "valid.token",
        user: { scopes: { demo: "admin" } }
    }),
}));

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("UpdateVersionForm.vue", () => {
    it("renders input fields (status, start date, end forecast date) and action button (submit and cancel)", async () => {
        server.use(...updateVersionHandlers);

        render(UpdateVersionForm, {
            props: { projectName: "demo", activeVersionId: "v1" },
            global: { plugins: [createTestingPinia()] },
        });

        expect(await screen.findByTestId("versionStatus")).toBeInTheDocument();
        expect(await screen.findByTestId("versionStartedInput")).toBeInTheDocument();
        expect(await screen.findByTestId("versionForecastInput")).toBeInTheDocument();
        expect(await screen.findByTestId("versionSubmitButton")).toBeInTheDocument();
        expect(await screen.findByTestId("versionCancelButton")).toBeInTheDocument();
    });

    it("loads version data (status, start, end forecast) and updates successfully", async () => {
        server.use(...updateVersionHandlers);

        const { emitted } = render(UpdateVersionForm, {
            props: { projectName: "demo", activeVersionId: "v1" },
            global: { plugins: [createTestingPinia()] },
        });

        // Wait for data
        expect(await screen.findByDisplayValue("2024-01-01")).toBeInTheDocument();
        expect(await screen.findByDisplayValue("Planned")).toBeInTheDocument();
        expect(await screen.findByDisplayValue("2024-02-01")).toBeInTheDocument();

        // Change status
        await fireEvent.update(screen.getByLabelText(/Version Status/i), "In Progress");
        await fireEvent.click(screen.getByRole("button", { name: /Update/i }));

        await waitFor(() => {
            expect(emitted()["version-updated"]).toBeTruthy();
        });
    });

    it("shows error if fetching workflow statuses fails", async () => {
        server.use(...updateVersionHandlers);

        render(UpdateVersionForm, {
            props: { projectName: "demo", activeVersionId: "v2" },
            global: { plugins: [createTestingPinia()] },
        });

        expect(await screen.findByText(/Error fetching status workflow/i)).toBeInTheDocument();
    });

    it("shows error if start date is after end forecast date", async () => {
        server.use(...updateVersionHandlers);

        render(UpdateVersionForm, {
            props: { projectName: "demo", activeVersionId: "v1" },
            global: { plugins: [createTestingPinia()] },
        });

        const startInput = await screen.findByLabelText(/Start Date/i);
        const forecastInput = await screen.findByLabelText(/End Forecast/i);

        await fireEvent.update(startInput, "2025-05-01");
        await fireEvent.update(forecastInput, "2025-04-01");
        await fireEvent.click(screen.getByRole("button", { name: /Update/i }));

        // You may need to add validation logic in the component for this case
        expect(await screen.findByText(/Start date cannot be after end forecast/i)).toBeInTheDocument();
    });
});
