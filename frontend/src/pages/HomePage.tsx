import { FlankingColumns } from "@/components/layout/FlankingColumns";
import { Hero } from "@/components/layout/Hero";
import { UploadForm } from "@/features/upload/UploadForm";

export function HomePage() {
  return (
    <div className="relative isolate">
      <FlankingColumns />
      <Hero
        title={
          <>
            Coarse-grain RNA <span className="text-accent">3D structure</span>
          </>
        }
      >
        <p>
          Upload an all-atom RNA structure and transform it into a coarse-grained
          representation using one of the models described in the literature, or define
          your own.
        </p>
      </Hero>
      <div className="mx-auto max-w-2xl px-4 pb-16">
        <UploadForm />
      </div>
    </div>
  );
}
