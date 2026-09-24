import { ImageOff } from "lucide-react";
import { useState } from "react";

interface ModelImageProps {
  src: string;
  modelName: string;
}

export function ModelImage({ src, modelName }: ModelImageProps) {
  const [failed, setFailed] = useState(false);

  return (
    <figure className="flex flex-col gap-2">
      <div className="flex aspect-[4/3] items-center justify-center overflow-hidden rounded-md border border-line-soft bg-white">
        {failed ? (
          <p className="flex flex-col items-center gap-2 font-mono text-label tracking-[0.15em] text-ink-3 uppercase">
            <ImageOff aria-hidden="true" className="size-6" />
            No preview
          </p>
        ) : (
          <img
            src={src}
            alt={`Conceptual representation of the ${modelName} model`}
            loading="lazy"
            onError={() => {
              setFailed(true);
            }}
            className="size-full object-contain"
          />
        )}
      </div>
      <figcaption className="text-xs text-ink-3">
        Conceptual representation of the mapping, not derived from simulations — bead
        positions after transformation may differ slightly. Sugar beads are shown in
        green, base beads in blue and phosphate beads in red.
      </figcaption>
    </figure>
  );
}
