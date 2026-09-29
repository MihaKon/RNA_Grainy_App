import { ImageOff } from "lucide-react";
import { useState } from "react";

interface ModelImageProps {
  src: string;
  modelName: string;
}

export function ModelImage({ src, modelName }: ModelImageProps) {
  const [failed, setFailed] = useState(false);

  return (
    <figure>
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
    </figure>
  );
}
