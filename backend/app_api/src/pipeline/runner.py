import time
import uuid
import json
from typing import Any, Dict, List
from src.modules.pipeline_lab.repositories.tweets_repository import TweetsRepository

class PipelineRunner:
    def __init__(
        self,
        pipeline_id: str,
        pipeline_name: str,
        pipeline_version: str,
        steps: List[Dict[str, Any]],
        runtime: Dict[str, Any] | None = None,
    ):
        self.pipeline_id = pipeline_id
        self.pipeline_name = pipeline_name
        self.pipeline_version = pipeline_version
        self.steps = steps
        self.runtime = runtime or {}
        self.tweets_repository = TweetsRepository()

    def run(self, text: str) -> Dict[str, Any]:
        context = {
            "tweet": {
                "text": text,
                "id": str(uuid.uuid4())
            },
            "outputs": {},
        }

        tweet_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())

        trace = []

        for step in self.steps:
            if not step.get("enabled", True):
                continue

            start_time = time.time()
            step_id = step["id"]

            # print(f"[PipelineRunner] Current context before step '{step_id}': {context}")

            try:
                input_mapping = step.get("input", {})
                # print(f"[PipelineRunner] Resolving inputs for step '{step_id}' with mapping: {input_mapping}")
                resolved_inputs = resolve_inputs(context, input_mapping)
                # print(f"[PipelineRunner] Resolved inputs for step '{step_id}': {resolved_inputs}")

                params = step.get("params", {})

                step_output = step["component"].run(
                    inputs=resolved_inputs,
                    params=params,
                    context=context,
                )

                output_path = step.get("output", step_id)

                set_path(context, output_path, step_output.result)
                context["outputs"][step_id] = step_output.result

                status = "success"
                if step_output.passed is False:
                    status = "blocked"


                trace.append({
                    "step_id": step_id,
                    "step_name": step.get("name", step_id),
                    "component": step.get("component_key"),
                    "status": status,
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "input": resolved_inputs,
                    "output_path": output_path,
                    "output": step_output.result,
                    "error": None,
                })

                if status == "blocked":
                    break

            except Exception as error:
                print("[Failed] " + str(error))
                trace.append({
                    "step_id": step_id,
                    "step_name": step.get("name", step_id),
                    "component": step.get("component_key"),
                    "status": "error",
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "input": step.get("input", {}),
                    "output": None,
                    "error": str(error),
                })

                if self.runtime.get("stop_on_error", True):
                    break

        self.tweets_repository.save_pipeline_execution({
            "tweet": {
                "id": tweet_id,
                "text": context["tweet"]["text"],
                "source": "twitter",
            },
            "run": {
                "id": run_id,
                "tweet_id": tweet_id,
                "pipeline_config": f"{self.pipeline_id}:{self.pipeline_version}",
                "status": "passed" if all(step["status"] == "success" for step in trace) else "blocked",
                "stopped_at": time.time(),
                "final_lat": self._extract_final_lat(context),
                "final_lon": self._extract_final_lon(context),
                "raw_json": {
                    "pipeline": {
                        "id": self.pipeline_id,
                        "name": self.pipeline_name,
                        "version": self.pipeline_version,
                    },
                    "outputs": context["outputs"],
                    "trace": trace,
                    # "final_output": final_output,
                },
            },
            "steps": trace,
        })

        tweet_count = self.tweets_repository.count_tweets()
        print(f"[PipelineRunner] Tweets in database: {tweet_count}")


        return {
            "run_id": str(uuid.uuid4()),
            "pipeline": {
                "id": self.pipeline_id,
                "name": self.pipeline_name,
                "version": self.pipeline_version,
            },
            "input": context["tweet"],
            "state": context,
            "outputs": context["outputs"],
            "trace": trace,
            "final_output": self._build_final_output(context),
        }

    def _extract_final_lat(self, context: Dict[str, Any]) -> float | None:
        return get_path(context, "outputs.geocoding.geocoded.lat")

    def _extract_final_lon(self, context: Dict[str, Any]) -> float | None:
        return get_path(context, "outputs.geocoding.geocoded.lon")

    def _build_final_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        relevance = get_path(context, "relevance")
        event_matching = get_path(context, "event_matching")

        return {
            "relevance": relevance,
            "event_matching": event_matching,
        }

def get_path(data: dict, path: str):
    keys = path.split(".")
    current = data

    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]

    return current


def set_path(data: dict, path: str, value):
    keys = path.split(".")
    current = data

    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def resolve_inputs(context: dict, input_mapping: dict) -> dict:
    resolved = {}

    for input_name, path in input_mapping.items():
        resolved[input_name] = get_path(context, path)

    return resolved