import { useMutation, useQuery } from "@tanstack/react-query";
import { type ReactNode, type SubmitEvent, useState } from "react";
import { useNavigate } from "react-router";

import { getErrorMessage } from "@/api/client";
import { coarseGrain, CUSTOM_MODEL_ID } from "@/api/coarseGrain";
import { appConfigQueryOptions, modelsQueryOptions } from "@/api/queries";
import type { AppConfig, ModelDocumentation } from "@/api/types";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { SelectField } from "@/components/ui/SelectField";
import { type TabItem, Tabs } from "@/components/ui/Tabs";
import { TextField } from "@/components/ui/TextField";
import { formatBeadsPerResidue, formatBytes, formatList } from "@/lib/format";
import type { ResultLocationState } from "@/features/results/resultState";
import { preloadStructureViewer } from "@/features/results/viewer/preload";

import { CustomModelInput } from "./CustomModelInput";
import { ExamplePicker } from "./ExamplePicker";
import { StructureFileInput } from "./StructureFileInput";
import {
  hasErrors,
  type SourceKind,
  toStructureSource,
  type UploadFormValues,
  validateUploadForm,
} from "./validation";

const SOURCE_TABS: readonly TabItem<SourceKind>[] = [
  { value: "file", label: "Upload file" },
  { value: "rcsb", label: "Fetch from PDB" },
  { value: "preset", label: "Use example" },
];

const INITIAL_VALUES: UploadFormValues = {
  sourceKind: "file",
  file: null,
  rcsbId: "",
  presetId: "",
  modelId: "",
  customModel: null,
  models: "",
  chains: "",
};

export function UploadForm() {
  const configQuery = useQuery(appConfigQueryOptions);
  const modelsQuery = useQuery(modelsQueryOptions);

  if (configQuery.isPending || modelsQuery.isPending) {
    return (
      <FormCard>
        <p role="status" className="p-6 eyebrow">
          Loading models…
        </p>
      </FormCard>
    );
  }

  if (configQuery.isError || modelsQuery.isError) {
    return (
      <Alert severity="error">
        <p className="font-medium">Could not load the available models.</p>
        <p className="text-ink-2">
          {getErrorMessage(configQuery.error ?? modelsQuery.error)}
        </p>
        <Button
          variant="ghost"
          className="mt-3"
          onClick={() => {
            void configQuery.refetch();
            void modelsQuery.refetch();
          }}
        >
          Try again
        </Button>
      </Alert>
    );
  }

  return <UploadFormContent config={configQuery.data} models={modelsQuery.data} />;
}

interface UploadFormContentProps {
  config: AppConfig;
  models: ModelDocumentation[];
}

function UploadFormContent({ config, models }: UploadFormContentProps) {
  const navigate = useNavigate();
  const [values, setValues] = useState(INITIAL_VALUES);
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const mutation = useMutation({ mutationFn: coarseGrain });

  const errors = submitAttempted ? validateUploadForm(values, config) : {};
  const sortedModels = models.toSorted((a, b) => a.name.localeCompare(b.name));
  const selectedModel = models.find((model) => model.id === values.modelId);
  const formats = config.supported_file_formats;

  const update = (patch: Partial<UploadFormValues>) => {
    setValues((current) => ({ ...current, ...patch }));
  };

  const handleSubmit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitAttempted(true);

    const source = toStructureSource(values);
    if (!source || hasErrors(validateUploadForm(values, config))) return;

    void preloadStructureViewer();

    mutation.mutate(
      {
        source,
        modelId: values.modelId,
        customModelJson: values.customModel?.json,
        models: values.models,
        chains: values.chains,
      },
      {
        onSuccess: (result) => {
          const state: ResultLocationState = { result };
          void navigate(`/results/${result.workspace_id}`, { state });
        },
      },
    );
  };

  const handleReset = () => {
    setValues(INITIAL_VALUES);
    setSubmitAttempted(false);
    mutation.reset();
  };

  return (
    <FormCard>
      <form noValidate onSubmit={handleSubmit} aria-busy={mutation.isPending}>
        <fieldset disabled={mutation.isPending} className="min-w-0">
          <Tabs
            label="Structure source"
            items={SOURCE_TABS}
            value={values.sourceKind}
            onChange={(sourceKind) => {
              update({ sourceKind });
            }}
            panelClassName="p-6"
          >
            {values.sourceKind === "file" && (
              <StructureFileInput
                file={values.file}
                accept={formats.map((format) => `.${format}`).join(",")}
                hint={`${formatList(formats.map((format) => format.toUpperCase()))} file, up to ${formatBytes(config.max_file_upload_size)}.`}
                error={errors.source}
                onChange={(file) => {
                  update({ file });
                }}
              />
            )}
            {values.sourceKind === "rcsb" && (
              <TextField
                label="PDB ID"
                placeholder="e.g. 1EHZ"
                value={values.rcsbId}
                maxLength={4}
                autoComplete="off"
                spellCheck={false}
                hint="The structure is downloaded in mmCIF format from the RCSB PDB."
                error={errors.source}
                onChange={(event) => {
                  update({ rcsbId: event.target.value });
                }}
              />
            )}
            {values.sourceKind === "preset" && (
              <ExamplePicker
                presetIds={config.preset_ids}
                value={values.presetId}
                error={errors.source}
                onChange={(presetId) => {
                  update({ presetId });
                }}
              />
            )}
          </Tabs>

          <div className="flex flex-col gap-5 border-t border-dashed border-line-soft p-6">
            <SelectField
              label="Coarse-grained model"
              value={values.modelId}
              error={errors.model}
              hint={
                selectedModel
                  ? formatBeadsPerResidue(selectedModel.beads_per_residue)
                  : undefined
              }
              onChange={(event) => {
                update({ modelId: event.target.value });
              }}
            >
              <option value="" disabled>
                Select a model
              </option>
              <optgroup label="Published models">
                {sortedModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Your own">
                <option value={CUSTOM_MODEL_ID}>Custom model (JSON)</option>
              </optgroup>
            </SelectField>

            {values.modelId === CUSTOM_MODEL_ID && (
              <CustomModelInput
                config={config}
                value={values.customModel}
                onChange={(customModel) => {
                  update({ customModel });
                }}
              />
            )}

            <div className="grid gap-5 lg:grid-cols-2">
              <TextField
                label="Chains"
                placeholder="e.g. A, B"
                value={values.chains}
                autoComplete="off"
                spellCheck={false}
                hint="Leave empty to include all chains."
                error={errors.chains}
                onChange={(event) => {
                  update({ chains: event.target.value });
                }}
              />
              <TextField
                label="Models"
                placeholder="e.g. 1, 2"
                value={values.models}
                inputMode="numeric"
                autoComplete="off"
                hint="Leave empty to include all models."
                error={errors.models}
                onChange={(event) => {
                  update({ models: event.target.value });
                }}
              />
            </div>

            {mutation.isError && (
              <Alert severity="error">{getErrorMessage(mutation.error)}</Alert>
            )}

            <div className="flex flex-wrap gap-3">
              <Button type="submit">
                {mutation.isPending ? "Processing…" : "Coarse-grain structure"}
              </Button>
              <Button variant="ghost" onClick={handleReset}>
                Reset
              </Button>
            </div>
          </div>
        </fieldset>
      </form>
    </FormCard>
  );
}

function FormCard({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-md border border-line-soft bg-white">
      {children}
    </div>
  );
}
