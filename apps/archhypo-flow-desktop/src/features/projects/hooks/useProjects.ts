import { useCallback, useEffect, useState } from "react";
import {
  createProject as createProjectRequest,
  deleteProject as deleteProjectRequest,
  listProjects,
  updateProjectSettings as updateProjectSettingsRequest,
} from "../api/projectClient";
import { loadProjects, saveProjects } from "../projectStorage";
import type { Project } from "../types";

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>(loadProjects);

  useEffect(() => {
    let active = true;
    void listProjects()
      .then(async (storedProjects) => {
        if (!active) return;
        if (storedProjects.length > 0) {
          setProjects(storedProjects);
          return;
        }

        const importedProjects: Project[] = [];
        for (const project of loadProjects()) {
          try {
            importedProjects.push(await createProjectRequest(project));
          } catch (error) {
            console.error("Could not import a locally stored project", error);
          }
        }
        if (active) setProjects(importedProjects);
      })
      .catch((error: unknown) => {
        console.error("Could not load projects from the local API", error);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    saveProjects(projects);
  }, [projects]);

  const createProject = useCallback(async (project: Project) => {
    const savedProject = await createProjectRequest(project);
    setProjects((current) => [
      savedProject,
      ...current.filter((item) => item.id !== savedProject.id),
    ]);
  }, []);

  const updateProjectSettings = useCallback(async (project: Project) => {
    const updatedProject = await updateProjectSettingsRequest(project);
    setProjects((current) =>
      current.map((item) => (item.id === updatedProject.id ? updatedProject : item)),
    );
  }, []);

  const deleteProject = useCallback(async (projectId: string) => {
    await deleteProjectRequest(projectId);
    setProjects((current) => current.filter((project) => project.id !== projectId));
  }, []);

  return {
    projects,
    createProject,
    updateProjectSettings,
    deleteProject,
  };
}
