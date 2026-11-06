import type { components } from "@/api/prefect";
import { cn } from "@/utils";
import { NOT_STARTED_STATES, type RunsSummary } from "./scatter-plot-utils";

type StateType = components["schemas"]["StateType"];

type ScatterPlotLegendProps = {
	summary: RunsSummary;
	emphasis: ReadonlySet<StateType>;
	onToggle: (state: StateType) => void;
};

const stateLabel = (state: StateType) =>
	state.charAt(0) + state.slice(1).toLowerCase();

export const ScatterPlotLegend = ({
	summary,
	emphasis,
	onToggle,
}: ScatterPlotLegendProps) => (
	<ul className="flex flex-wrap gap-1.5" aria-label="Highlight runs by state">
		{summary.byState.map(({ state, count }) => {
			const pressed = emphasis.has(state);
			const color = `var(--state-${state.toLowerCase()}-500)`;
			return (
				<li key={state}>
					<button
						type="button"
						aria-pressed={pressed}
						onClick={() => onToggle(state)}
						className={cn(
							"inline-flex h-11 items-center gap-1.5 rounded-md border px-2.5 text-xs transition-colors md:h-8",
							pressed
								? "border-foreground/40 bg-accent"
								: "border-transparent hover:bg-muted",
							emphasis.size > 0 && !pressed && "text-muted-foreground",
						)}
					>
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
					</button>
				</li>
			);
		})}
	</ul>
);
