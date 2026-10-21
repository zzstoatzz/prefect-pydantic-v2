import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { buildFLowDetailsQuery } from "@/api/flows";
import { Icon } from "@/components/ui/icons";
import { Skeleton } from "@/components/ui/skeleton";

type FlowLinkProps = {
	flowId: string;
};

export const FlowLink = ({ flowId }: FlowLinkProps) => {
	return (
		<Suspense fallback={<Skeleton className="h-4 w-full" />}>
			<FlowLinkImplementation flowId={flowId} />
		</Suspense>
	);
};

const FlowLinkImplementation = ({ flowId }: FlowLinkProps) => {
	const { data: flow } = useSuspenseQuery(buildFLowDetailsQuery(flowId));

	return (
		<div className="flex min-w-0 max-w-full items-center gap-1 text-xs">
			Flow
			<Link
				to="/flows/flow/$id"
				params={{ id: flow.id }}
				className="flex min-w-0 items-center gap-1"
				title={flow.name}
			>
				<Icon id="Workflow" className="size-4 shrink-0" />
				<span className="truncate">{flow.name}</span>
			</Link>
		</div>
	);
};
