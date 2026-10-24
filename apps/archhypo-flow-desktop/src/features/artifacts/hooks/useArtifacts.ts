import { useCallback, useEffect, useState } from "react";
import { listArtifacts } from "../api/artifactClient";
import type { ArtifactSummary } from "../types";

export function useArtifacts() {
  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setArtifacts(await listArtifacts());
      setError(false);
    } catch (loadError) {
      console.error("Could not load ArchHypo artifacts", loadError);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { artifacts, loading, error, reload };
}
