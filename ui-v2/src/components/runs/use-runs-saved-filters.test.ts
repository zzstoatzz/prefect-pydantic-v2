/* eslint-disable @typescript-eslint/unbound-method */
import { expect, it, vi } from "vitest";
import { defaultFilterSearch } from "./use-runs-saved-filters";

const withStoredFilters = (
	defaultFilterId: string,
	savedFilters: unknown[],
	check: () => void,
) =>
	vi.mocked(localStorage.getItem).withImplementation(
		(key) =>
			({
				"prefect-ui-v2-default-filter-id": JSON.stringify(defaultFilterId),
				"prefect-ui-v2-saved-filters": JSON.stringify(savedFilters),
			})[key] ?? null,
		check,
	);

it("applies Past week to a runs URL without filters", () => {
	expect(defaultFilterSearch({ state: "", flows: "" })).toMatchObject({
		range: "past-7-days",
		page: 1,
		"task-runs-page": 1,
	});
});

it("applies the user's default saved filter, or Past week once it is deleted", () => {
	const mine = {
		id: "mine",
		name: "Failed this month",
		filters: { range: "past-30-days", state: ["Failed"] },
	};
	withStoredFilters("mine", [mine], () => {
		expect(defaultFilterSearch({})).toMatchObject({
			range: "past-30-days",
			state: "Failed",
		});
	});
	withStoredFilters("deleted", [mine], () => {
		expect(defaultFilterSearch({})).toMatchObject({ range: "past-7-days" });
	});
});

it("leaves a runs URL that already filters the page", () => {
	expect(defaultFilterSearch({ tags: "nightly" })).toBeUndefined();
	expect(
		defaultFilterSearch({ start: "2026-11-01T00:00:00Z" }),
	).toBeUndefined();
});
