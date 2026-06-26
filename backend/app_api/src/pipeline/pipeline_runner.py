import time
from typing import Any

from src.components.registry import COMPONENT_REGISTRY
from src.pipeline.utils import resolve_inputs, set_path
from src.repositories.pipeline_step_repository import create_step_execution


class PipelineRunner:
    """
    Run a tweet on a pipeline config.
    """
    def __init__(self, pipeline_config: dict[str, Any]):
        self.pipeline_config = pipeline_config
        self.steps = pipeline_config.get("steps", [])
        self.runtime = pipeline_config.get("runtime", {})

    def run_tweet(
        self,
        tweet_id: str,
        run_id: str,
        text: str,
    ) -> dict[str, Any]:
        context = {
            "tweet": {
                "id": tweet_id,
                "content": text,
            },
            "outputs": {},
        }

        trace = []

        for step_index, step in enumerate(self.steps):
            if not step.get("enabled", True):
                continue

            step_id = step["id"]
            component_key = step["component_key"]
            start_time = time.time()

            try:
                component_cls = COMPONENT_REGISTRY[component_key]
                component = component_cls()

                inputs = resolve_inputs(context, step.get("input", {}))

                output = component.run(
                    inputs=inputs,
                    params=step.get("params", {}),
                    context=context,
                )

                output_path = step.get("output", f"outputs.{step_id}")
                set_path(context, output_path, output.result)
                context["outputs"][step_id] = output.result

                status = "success" if output.passed else "blocked"

                step_record = {
                    "run_id": run_id,
                    "tweet_id": tweet_id,
                    "step_name": step_id,
                    "status": status,
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "input_json": inputs,
                    "output_json": output.result,
                    "step_index": step_index,
                }

                create_step_execution(step_record)
                trace.append(step_record)

                if status == "blocked":
                    break

            except Exception as e:
                step_record = {
                    "run_id": run_id,
                    "tweet_id": tweet_id,
                    "step_name": step_id,
                    "status": "error",
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "input_json": step.get("input", {}),
                    "output_json": {"error": str(e)},
                    "step_index": step_index,
                }

                create_step_execution(step_record)
                trace.append(step_record)

                if self.runtime.get("stop_on_error", True):
                    break

        return {
            "tweet_id": tweet_id,
            "run_id": run_id,
            "context": context,
            "trace": trace,
        }
