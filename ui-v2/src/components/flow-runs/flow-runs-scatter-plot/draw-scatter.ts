import type { components } from "@/api/prefect";
import { NOT_STARTED_STATES, type PlotPoint } from "./scatter-plot-utils";

type StateType = components["schemas"]["StateType"];

export type ScatterGeometry = {
	width: number;
	height: number;
	left: number;
	right: number;
	top: number;
	/** Bottom edge of the log-scale duration area. */
	logBottom: number;
	/** Center line of the lane for runs with no recorded duration. */
	laneY: number;
	/** Baseline under the zero lane, where time labels hang. */
	axisY: number;
};

export type ScatterPalette = {
	border: string;
	muted: string;
	foreground: string;
	state: Record<StateType, string>;
};

export type ScatterScene = {
	geometry: ScatterGeometry;
	points: readonly PlotPoint[];
	radius: number;
	durationTicks: readonly { y: number; label: string }[];
	timeTicks: readonly { x: number; label: string }[];
	/** Right edge of the strip marking runs the row limit left out. */
	unloadedUntilX: number | undefined;
	nowX: number | undefined;
	activeId: string | undefined;
	brush: { from: number; to: number } | undefined;
	palette: ScatterPalette;
	fontFamily: string;
};

const LABEL_FONT_SIZE = 11;

export const drawScatter = (
	ctx: CanvasRenderingContext2D,
	scene: ScatterScene,
): void => {
	const { geometry: g, palette } = scene;
	ctx.clearRect(0, 0, g.width, g.height);
	ctx.font = `${LABEL_FONT_SIZE}px ${scene.fontFamily}`;
	ctx.textBaseline = "middle";

	drawUnloaded(ctx, scene);
	drawGrid(ctx, scene);
	drawTimeAxis(ctx, scene);

	if (scene.nowX !== undefined) {
		ctx.save();
		ctx.strokeStyle = palette.muted;
		ctx.globalAlpha = 0.6;
		ctx.setLineDash([3, 3]);
		ctx.beginPath();
		ctx.moveTo(Math.round(scene.nowX) + 0.5, g.top);
		ctx.lineTo(Math.round(scene.nowX) + 0.5, g.axisY);
		ctx.stroke();
		ctx.restore();
	}

	drawPoints(ctx, scene);
	drawActive(ctx, scene);
	drawBrush(ctx, scene);
};

const drawUnloaded = (ctx: CanvasRenderingContext2D, scene: ScatterScene) => {
	const { geometry: g, palette, unloadedUntilX } = scene;
	if (unloadedUntilX === undefined || unloadedUntilX <= g.left) return;
	const right = Math.min(unloadedUntilX, g.right);
	ctx.save();
	ctx.beginPath();
	ctx.rect(g.left, g.top, right - g.left, g.axisY - g.top);
	ctx.clip();
	ctx.strokeStyle = palette.border;
	ctx.globalAlpha = 0.5;
	ctx.lineWidth = 1;
	ctx.beginPath();
	for (let x = g.left - g.height; x < right; x += 8) {
		ctx.moveTo(x, g.axisY);
		ctx.lineTo(x + (g.axisY - g.top), g.top);
	}
	ctx.stroke();
	ctx.restore();
};

const drawGrid = (ctx: CanvasRenderingContext2D, scene: ScatterScene) => {
	const { geometry: g, palette } = scene;
	ctx.save();
	ctx.lineWidth = 1;
	ctx.strokeStyle = palette.border;
	ctx.fillStyle = palette.muted;
	ctx.textAlign = "right";
	for (const tick of scene.durationTicks) {
		const y = Math.round(tick.y) + 0.5;
		ctx.beginPath();
		ctx.moveTo(g.left, y);
		ctx.lineTo(g.right, y);
		ctx.stroke();
		ctx.fillText(tick.label, g.left - 8, y);
	}
	ctx.setLineDash([2, 3]);
	const laneTop = Math.round(g.logBottom + (g.laneY - g.logBottom) / 2) + 0.5;
	ctx.beginPath();
	ctx.moveTo(g.left, laneTop);
	ctx.lineTo(g.right, laneTop);
	ctx.stroke();
	ctx.setLineDash([]);
	ctx.fillText("0s", g.left - 8, g.laneY);
	ctx.restore();
};

const drawTimeAxis = (ctx: CanvasRenderingContext2D, scene: ScatterScene) => {
	const { geometry: g, palette } = scene;
	ctx.save();
	ctx.strokeStyle = palette.border;
	ctx.beginPath();
	ctx.moveTo(g.left, Math.round(g.axisY) + 0.5);
	ctx.lineTo(g.right, Math.round(g.axisY) + 0.5);
	ctx.stroke();
	ctx.fillStyle = palette.muted;
	ctx.textAlign = "center";
	ctx.textBaseline = "top";
	let lastRight = Number.NEGATIVE_INFINITY;
	for (const tick of scene.timeTicks) {
		const half = ctx.measureText(tick.label).width / 2;
		const x = Math.min(Math.max(tick.x, g.left + half), g.width - half - 1);
		if (x - half < lastRight + 12) continue;
		ctx.fillText(tick.label, x, g.axisY + 6);
		lastRight = x + half;
	}
	ctx.restore();
};

const drawPoints = (ctx: CanvasRenderingContext2D, scene: ScatterScene) => {
	const { palette, radius } = scene;
	ctx.save();
	ctx.lineWidth = 1.75;
	for (const { run, x, y } of scene.points) {
		const color = palette.state[run.state_type];
		const ring = NOT_STARTED_STATES.has(run.state_type);
		const quiet = run.state_type === "COMPLETED";
		ctx.globalAlpha = ring ? 1 : quiet ? 0.55 : 0.9;
		ctx.beginPath();
		ctx.arc(x, y, ring ? radius - 0.5 : radius, 0, Math.PI * 2);
		if (ring) {
			ctx.strokeStyle = color;
			ctx.stroke();
		} else {
			ctx.fillStyle = color;
			ctx.fill();
		}
	}
	ctx.restore();
};

const drawActive = (ctx: CanvasRenderingContext2D, scene: ScatterScene) => {
	const { geometry: g, palette, activeId } = scene;
	if (activeId === undefined) return;
	const active = scene.points.find((point) => point.run.id === activeId);
	if (!active) return;
	ctx.save();
	ctx.strokeStyle = palette.muted;
	ctx.globalAlpha = 0.5;
	ctx.beginPath();
	ctx.moveTo(Math.round(active.x) + 0.5, g.top);
	ctx.lineTo(Math.round(active.x) + 0.5, g.axisY);
	ctx.stroke();
	ctx.globalAlpha = 1;
	ctx.fillStyle = palette.state[active.run.state_type];
	ctx.beginPath();
	ctx.arc(active.x, active.y, scene.radius + 1.5, 0, Math.PI * 2);
	ctx.fill();
	ctx.lineWidth = 2;
	ctx.strokeStyle = palette.foreground;
	ctx.beginPath();
	ctx.arc(active.x, active.y, scene.radius + 4, 0, Math.PI * 2);
	ctx.stroke();
	ctx.restore();
};

const drawBrush = (ctx: CanvasRenderingContext2D, scene: ScatterScene) => {
	const { geometry: g, palette, brush } = scene;
	if (!brush) return;
	const from = Math.max(g.left, Math.min(brush.from, brush.to));
	const to = Math.min(g.right, Math.max(brush.from, brush.to));
	ctx.save();
	ctx.fillStyle = palette.foreground;
	ctx.globalAlpha = 0.08;
	ctx.fillRect(from, g.top, to - from, g.axisY - g.top);
	ctx.globalAlpha = 0.6;
	ctx.strokeStyle = palette.foreground;
	ctx.beginPath();
	ctx.moveTo(Math.round(from) + 0.5, g.top);
	ctx.lineTo(Math.round(from) + 0.5, g.axisY);
	ctx.moveTo(Math.round(to) - 0.5, g.top);
	ctx.lineTo(Math.round(to) - 0.5, g.axisY);
	ctx.stroke();
	ctx.restore();
};
