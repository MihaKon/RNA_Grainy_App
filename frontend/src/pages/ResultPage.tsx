import { Link, useLocation, useParams } from "react-router";

import { PageHero } from "@/components/layout/PageHero";
import { readResultState } from "@/features/results/resultState";
import { ResultView } from "@/features/results/ResultView";

export function ResultPage() {
  const { workspaceId } = useParams();
  const location = useLocation();
  const result = readResultState(location.state, workspaceId);

  if (!result) {
    return (
      <PageHero
        eyebrow="Result"
        title={
          <>
            Result <span className="text-accent">not available</span>
          </>
        }
      >
        <p>
          Results are only available right after processing. Please coarse-grain the
          structure again.
        </p>
        <Link to="/" className="mt-4 inline-block text-accent hover:text-accent-hover">
          ← New structure
        </Link>
      </PageHero>
    );
  }

  return <ResultView key={result.workspace_id} result={result} />;
}
