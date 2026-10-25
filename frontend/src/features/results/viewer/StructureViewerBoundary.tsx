import { Component, type ReactNode } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";

interface StructureViewerBoundaryProps {
  children: ReactNode;
}

interface StructureViewerBoundaryState {
  hasError: boolean;
}

export class StructureViewerBoundary extends Component<
  StructureViewerBoundaryProps,
  StructureViewerBoundaryState
> {
  state: StructureViewerBoundaryState = { hasError: false };

  static getDerivedStateFromError(): StructureViewerBoundaryState {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <Alert severity="error">
          <p className="font-medium">The structure viewer could not be loaded.</p>
          <p className="mt-1 text-ink-2">
            You can still download the CG model above. Reload the page to try again.
          </p>
          <Button
            variant="ghost"
            className="mt-3"
            onClick={() => {
              window.location.reload();
            }}
          >
            Reload page
          </Button>
        </Alert>
      );
    }

    return this.props.children;
  }
}
