"use client";
import { useEffect, useState } from "react";
import ProjectCard from "./_components/ProjectCard";
import { Button } from "~/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from "~/components/ui/dialog";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import UserImage from "~/components/UserImage";
import { useUser } from "@clerk/nextjs";
import { api } from "~/trpc/react";
import { useRouter } from "next/navigation";

export default function Home() {
  const { user } = useUser();
  const router = useRouter();
  const [projects, setProjects] = useState<Array<{ id: string; name: string }>>(
    [],
  );
  const [projectName, setProjectName] = useState("");

  const {
    data: projectsData,
    refetch: refetchProjects,
    error: projectsError,
  } = api.project.getProjects.useQuery();
  const { mutate: createProject, error: createProjectError } =
    api.project.createProject.useMutation({
      onSuccess: (data) => {
        console.log("Project created");
        setProjectName("");
        router.push(`/projects/${data.id}`);
      },
    });

  useEffect(() => {
    if (projectsData) {
      setProjects(projectsData);
    }
  }, [projectsData]);

  const handleCreateProject = () => {
    createProject({ projectName });
    setProjects([...projects, { id: "1", name: projectName }]);
  };

  useEffect(() => {
    console.log("projectsError", projectsError);
  }, [projectsError]);

  useEffect(() => {
    console.log("createProjectError", createProjectError);
  }, [createProjectError]);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex gap-4">
        <UserImage imageUrl={user?.imageUrl} />
        <div>
          <div className="text-lg font-medium">{user?.fullName}</div>
          <div className="text-sm text-muted-foreground">
            {user?.emailAddresses[0]?.emailAddress}
          </div>
        </div>
      </div>
      <div>
        <div className="mb-4 flex items-center justify-between">
          <div className="text-lg font-medium">My projects</div>
          <Dialog>
            <DialogTrigger asChild>
              <Button>Create project</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create project</DialogTitle>
              </DialogHeader>
              <div className="flex flex-col gap-2 py-4">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="project-name">Project name</Label>
                  <Input
                    id="project-name"
                    placeholder="Palo Alto project"
                    autoComplete="off"
                    value={projectName}
                    onChange={(e) => {
                      setProjectName(e.target.value);
                    }}
                  />
                </div>
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button onClick={handleCreateProject}>Create</Button>
                </DialogClose>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
        <div className="flex flex-col gap-2">
          {projects?.map((project) => (
            <ProjectCard key={project.id} id={project.id} name={project.name} />
          ))}
        </div>
      </div>
    </div>
  );
}