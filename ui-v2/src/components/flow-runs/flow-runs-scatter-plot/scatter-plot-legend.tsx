import { type MouseEvent, useRef } from "react";
import type { components } from "@/api/prefect";
import type { FlowRunState } from "@/components/flow-runs/flow-runs-list";
import { cn } from "@/utils";
import {
	isolatedStateType,
	NOT_STARTED_STATES,
	type StateCount,
	stateNamesOfType,
	withoutStateType,
} from "./scatter-plot-utils";

type StateType = components["schemas"]["StateType"];

type ScatterPlotLegendProps = {
	/** States to show, with their run counts, in legend order. */
	counts: readonly StateCount[];
	/** The page's state filter, by state name; empty means every state. */
	selectedStates?: ReadonlySet<FlowRunState>;
	/** Omit to show the legend as a key without filtering. */
	onSelectedStatesChange?: (states: Set<FlowRunState>) => void;
};

const stateLabel = (state: StateType) =>
	state.charAt(0) + state.slice(1).toLowerCase();

const chipClassName =
	"inline-flex h-11 items-center gap-1.5 rounded-md border px-2.5 text-xs md:h-8";

const ChipContent = ({ state, count }: { state: StateType; count: number }) => {
	const color = `var(--state-${state.toLowerCase()}-500)`;
	return (
		<>
			<span
				aria-hidden
				className="size-2.5 shrink-0 rounded-full"
				style={
					NOT_STARTED_STATES.has(state)
						? { boxShadow: `inset 0 0 0 1.5px ${color}` }
						: { backgroundColor: color }
				}
			/>
			{stateLabel(state)}
			<span className="text-muted-foreground tabular-nums">
				{count.toLocaleString()}
			</span>
		</>
	);
};

export const ScatterPlotLegend = ({
	counts,
	selectedStates = new Set(),
	onSelectedStatesChange,
}: ScatterPlotLegendProps) => {
	const restoreTo = useRef<Set<FlowRunState> | undefined>(undefined);

	if (!onSelectedStatesChange) {
		return (
			<ul className="flex flex-wrap gap-1.5" aria-label="Runs by state">
				{counts.map(({ state, count }) => (
					<li key={state} className={cn(chipClassName, "border-transparent")}>
						<ChipContent state={state} count={count} />
					</li>
				))}
			</ul>
		);
	}

	const isolated = isolatedStateType(selectedStates);
	const onChipClick = (state: StateType, event: MouseEvent) => {
		if (event.shiftKey) {
			const remaining = withoutStateType(selectedStates, state);
			if (remaining.size > 0) onSelectedStatesChange(remaining);
			return;
		}
		if (state === isolated) {
			onSelectedStatesChange(restoreTo.current ?? new Set());
			restoreTo.current = undefined;
			return;
		}
		if (isolated === undefined) restoreTo.current = new Set(selectedStates);
		onSelectedStatesChange(stateNamesOfType(state));
	};

	return (
		<ul className="flex flex-wrap gap-1.5" aria-label="Filter runs by state">
			{counts.map(({ state, count }) => {
				const pressed = state === isolated;
				return (
					<li key={state}>
						<button
							type="button"
							aria-pressed={pressed}
							title={
								pressed
									? "Show the other states again"
									: `Show only ${stateLabel(state).toLowerCase()} runs. Shift-click to hide them.`
							}
							onClick={(event) => onChipClick(state, event)}
							className={cn(
								chipClassName,
								"transition-colors",
								pressed
									? "border-foreground/40 bg-accent"
									: "border-transparent hover:bg-muted",
							)}
						>
							<ChipContent state={state} count={count} />
						</button>
					</li>
				);
			})}
		</ul>
	);
};
