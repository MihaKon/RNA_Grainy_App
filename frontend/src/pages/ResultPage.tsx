import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useParams } from "react-router";

import { ApiError, getErrorMessage } from "@/api/client";
import { resultQueryOptions } from "@/api/results";
import { Hero } from "@/components/layout/Hero";
import { Button } from "@/components/ui/Button";
import { readResultState } from "@/features/results/resultState";
import { ResultView } from "@/features/results/ResultView";

export function ResultPage() {
  const { workspaceId = "" } = useParams();
  const location = useLocation();
  const resultQuery = useQuery({
    ...resultQueryOptions(workspaceId),
    initialData: readResultState(location.state, workspaceId) ?? undefined,
    enabled: Boolean(workspaceId),
  });

  if (resultQuery.data) {
    return <ResultView key={resultQuery.data.workspace_id} result={resultQuery.data} />;
  }

  if (resultQuery.isPending && workspaceId) {
    return (
      <Hero eyebrow="Result" title="Loading result">
        <p role="status">Loading conversion summary…</p>
      </Hero>
    );
  }

  const unavailable =
    !workspaceId ||
    (resultQuery.error instanceof ApiError &&
      (resultQuery.error.status === 404 || resultQuery.error.status === 422));

  return (
    <Hero
      eyebrow="Result"
      title={
        unavailable ? (
          <>
            Result <span className="text-accent">not available</span>
          </>
        ) : (
          <>
            Could not <span className="text-accent">load result</span>
          </>
        )
      }
    >
      <p>
        {unavailable
          ? "This result does not exist or is no longer available. Please process the structure again."
          : getErrorMessage(resultQuery.error)}
      </p>
      {!unavailable && (
        <Button
          variant="ghost"
          className="mt-4"
          disabled={resultQuery.isFetching}
          onClick={() => {
            void resultQuery.refetch();
          }}
        >
          Try again
        </Button>
      )}
      <Link to="/" className="mt-4 block text-accent hover:text-accent-hover">
        ← Process another structure
      </Link>
    </Hero>
  );
}
