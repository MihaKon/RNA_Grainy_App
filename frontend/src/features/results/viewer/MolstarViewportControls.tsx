import { PluginStateObject } from "molstar/lib/mol-plugin-state/objects";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { PluginReactContext } from "molstar/lib/mol-plugin-ui/base";
import { ViewportControls } from "molstar/lib/mol-plugin-ui/viewport";
import { useCallback, useContext, useSyncExternalStore } from "react";

export function MolstarViewportControls() {
  const plugin = useContext(PluginReactContext);

  const subscribe = useCallback(
    (onChange: () => void) => {
      const subscription = plugin.state.data.events.changed.subscribe(onChange);

      return () => {
        subscription.unsubscribe();
      };
    },
    [plugin],
  );

  const getSnapshot = useCallback(() => {
    const state = plugin.state.data;
    const models = state.selectQ((q) =>
      q
        .ofType(PluginStateObject.Molecule.Model)
        .withTransformer(StateTransforms.Model.ModelFromTrajectory),
    );

    if (models.length < 2) return "";

    const model = models[0];
    if (!model) return "";

    const [trajectory] = state.selectQ((q) =>
      q.byRef(model.transform.parent).ofType(PluginStateObject.Molecule.Trajectory),
    );

    const total = trajectory?.obj?.data.frameCount ?? 0;
    if (total < 2) return "";

    const index = model.transform.params?.modelIndex;
    if (index === undefined) return "";

    const position = index + 1;
    const number = model.obj?.data.modelNum ?? position;

    return number === position
      ? `Model ${String(position)} / ${String(total)}`
      : `Model ${String(number)} (${String(position)} of ${String(total)})`;
  }, [plugin]);

  const label = useSyncExternalStore(subscribe, getSnapshot, () => "");

  return (
    <>
      <ViewportControls />
      {label && <div className="rnagrainy-model-indicator">{label}</div>}
    </>
  );
}
