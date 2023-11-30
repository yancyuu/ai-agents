import enum
import os
from pathlib import Path
from controller.create_code.prompts import Prompts
from agent_protocol import Agent, Step, Task


class AgentsType(str, enum.Enum):
    PLAN = "plan"
    SPECIFY_FILE_PATHS = "specify_file_paths"
    GENERATE_CODE = "generate_code"

class AgentsAPI:

    def __init__(self) -> None:
        super().__init__()
        self.prompt = Prompts()

    async def _generate_shared_deps(self, step: Step) -> Step:
        task = await Agent.db.get_task(step.task_id)
        shared_deps = self.prompt.plan(task.input)
        await Agent.db.create_step(
            step.task_id,
            AgentsType.SPECIFY_FILE_PATHS,
            additional_properties={
                "shared_deps": shared_deps,
            },
        )
        step.output = shared_deps
        return step

    async def _generate_file_paths(self, task: Task, step: Step) -> Step:
        shared_deps = step.additional_properties["shared_deps"]
        file_paths = self.prompt.specify_file_paths(task.input, shared_deps)
        for file_path in file_paths[:-1]:
            await Agent.db.create_step(
                task.task_id,
                f"Generate code for {file_path}",
                additional_properties={
                    "shared_deps": shared_deps,
                    "file_path": file_paths[-1],
                },
            )

        await Agent.db.create_step(
            task.task_id,
            f"Generate code for {file_paths[-1]}",
            is_last=True,
            additional_properties={
                "shared_deps": shared_deps,
                "file_path": file_paths[-1],
            },
        )

        step.output = f"File paths are: {str(file_paths)}"
        return step


    async def _generate_code(self, task: Task, step: Step) -> Step:
        shared_deps = step.additional_properties["shared_deps"]
        file_path = step.additional_properties["file_path"]

        code = await self.prompt.generate_code(task.input, shared_deps, file_path)
        step.output = code

        # write_file(os.path.join(Agent.get_workspace(task.task_id), file_path), code)
        path = Path("./" + file_path)
        await Agent.db.create_artifact(
            task_id=task.task_id,
            step_id=step.step_id,
            relative_path=str(path.parent),
            file_name=path.name,
        )
        return step

    async def task_handler(self, task: Task) -> None:
        if not task.input:
            raise Exception("No task prompt")
        await Agent.db.create_step(task.task_id, AgentsType.PLAN)

    async def step_handler(self, step: Step):
        task = await Agent.db.get_task(step.task_id)
        if step.name == AgentsType.PLAN:
            return await self._generate_shared_deps(step)
        elif step.name == AgentsType.SPECIFY_FILE_PATHS:
            return await self._generate_file_paths(task, step)
        else:
            return await self._generate_code(task, step)


