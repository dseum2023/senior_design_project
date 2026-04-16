"""
Fairness Controller
Ensures all LLM models receive equivalent compute resources for unbiased benchmarking.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_CONFIG = {
    "fairness_version": "1.0",
    "ollama_parameters": {
        "num_ctx": 4096,
        "num_gpu": 999,
        "num_thread": 8,
        "num_predict": 16384,
        "temperature": 0.3,
        "top_p": 0.9,
        "top_k": 40,
    },
    "model_overrides": {
        "qwen3": {
            "think": False,
            "justification": (
                "Disables hidden chain-of-thought to prevent exhausting token budget "
                "on invisible reasoning."
            ),
        }
    },
    "cooldown": {
        "between_models_seconds": 60,
        "between_questions_seconds": 0,
        "gpu_temp_threshold_c": 55,
        "gpu_temp_wait_max_seconds": 300,
    },
    "warmup": {
        "enabled": True,
        "warmup_prompt": "What is 2+2?",
    },
    "system_validation": {
        "enabled": True,
        "max_gpu_util_percent": 5,
        "max_cpu_util_percent": 20,
        "check_no_other_models_loaded": True,
        "validation_sample_seconds": 3,
    },
}


class FairnessController:
    """
    Controls compute fairness across model benchmark runs.

    Usage:
        fc = FairnessController("config/fairness_config.json")
        options = fc.build_ollama_options("qwen3:4b")
        valid, snapshot = fc.validate_system_state()
        fc.unload_models(ollama_client)
        warmup_meta = fc.warmup_model(ollama_client)
    """

    def __init__(self, config_path: str = "config/fairness_config.json"):
        self._config = dict(DEFAULT_CONFIG)
        self._warmup_metadata: Optional[Dict[str, Any]] = None
        self._validation_metadata: Optional[Dict[str, Any]] = None
        self._cooldown_metadata: Optional[Dict[str, Any]] = None

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # Deep-merge top-level keys
                for key, value in loaded.items():
                    if isinstance(value, dict) and isinstance(self._config.get(key), dict):
                        self._config[key] = {**self._config[key], **value}
                    else:
                        self._config[key] = value
                print(f"[Fairness] Loaded config from {config_path}")
            except Exception as e:
                print(f"[Fairness] Warning: could not load {config_path}: {e}. Using defaults.")
        else:
            print(f"[Fairness] Config not found at {config_path}, using built-in defaults.")

        self._nvml_available = False
        self._gpu_handle = None
        self._init_nvml()

    # ------------------------------------------------------------------
    # NVML helpers (reuse pattern from ResourceMonitor)
    # ------------------------------------------------------------------

    def _init_nvml(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            self._gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            self._nvml_available = True
        except Exception:
            self._nvml_available = False
            self._gpu_handle = None

    def _shutdown_nvml(self):
        if self._nvml_available:
            try:
                import pynvml
                pynvml.nvmlShutdown()
            except Exception:
                pass

    def _read_gpu_temp(self) -> Optional[float]:
        if not self._nvml_available or self._gpu_handle is None:
            return None
        try:
            import pynvml
            return float(pynvml.nvmlDeviceGetTemperature(
                self._gpu_handle, pynvml.NVML_TEMPERATURE_GPU
            ))
        except Exception:
            return None

    def _read_gpu_util(self) -> Optional[float]:
        if not self._nvml_available or self._gpu_handle is None:
            return None
        try:
            import pynvml
            util = pynvml.nvmlDeviceGetUtilizationRates(self._gpu_handle)
            return float(util.gpu)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Core public API
    # ------------------------------------------------------------------

    def build_ollama_options(self, model_name: str) -> Dict[str, Any]:
        """Return the standardized Ollama options dict for the given model."""
        options: Dict[str, Any] = dict(self._config["ollama_parameters"])

        # Apply model-specific overrides
        overrides_map: Dict[str, Any] = self._config.get("model_overrides", {})
        applied_overrides: Dict[str, Any] = {}
        for key_fragment, override in overrides_map.items():
            if key_fragment.lower() in model_name.lower():
                for param, val in override.items():
                    if param != "justification":
                        options[param] = val
                        applied_overrides[param] = {
                            "value": val,
                            "justification": override.get("justification", ""),
                        }

        if applied_overrides:
            print(f"[Fairness] Model overrides for '{model_name}': {list(applied_overrides.keys())}")

        return options

    def validate_system_state(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Sample CPU/GPU to confirm system is idle before benchmarking.
        Also checks Ollama /api/ps for models already loaded in VRAM.

        Returns (passed, snapshot_dict).
        """
        cfg = self._config.get("system_validation", {})
        if not cfg.get("enabled", True):
            snapshot = {"skipped": True, "reason": "system_validation disabled in config"}
            self._validation_metadata = snapshot
            return True, snapshot

        print("[Fairness] Validating system state...")

        import psutil
        sample_seconds = cfg.get("validation_sample_seconds", 3)

        # Sample CPU
        psutil.cpu_percent(interval=None)  # prime
        time.sleep(sample_seconds)
        cpu_util = psutil.cpu_percent(interval=None)

        # Sample GPU
        gpu_util = self._read_gpu_util()
        gpu_temp = self._read_gpu_temp()

        max_gpu = cfg.get("max_gpu_util_percent", 5)
        max_cpu = cfg.get("max_cpu_util_percent", 20)

        passed = True
        warnings: List[str] = []

        if gpu_util is not None and gpu_util > max_gpu:
            warnings.append(
                f"GPU utilization {gpu_util:.1f}% exceeds threshold {max_gpu}%"
            )
            passed = False

        if cpu_util > max_cpu:
            warnings.append(
                f"CPU utilization {cpu_util:.1f}% exceeds threshold {max_cpu}%"
            )
            passed = False

        # Check Ollama for loaded models
        loaded_models: List[str] = []
        if cfg.get("check_no_other_models_loaded", True):
            loaded_models = self._list_loaded_models_internal()
            if loaded_models:
                warnings.append(f"Other models loaded in Ollama VRAM: {loaded_models}")
                # Don't hard-fail — we'll unload them next

        snapshot = {
            "passed": passed,
            "cpu_util_percent": round(cpu_util, 1),
            "gpu_util_percent": round(gpu_util, 1) if gpu_util is not None else None,
            "gpu_temp_c": round(gpu_temp, 1) if gpu_temp is not None else None,
            "other_models_loaded": loaded_models,
            "warnings": warnings,
            "validation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self._validation_metadata = snapshot

        if warnings:
            for w in warnings:
                print(f"[Fairness] Warning: {w}")
        if passed:
            print("[Fairness] System state OK.")
        else:
            print("[Fairness] System not fully idle — proceeding with caution.")

        return passed, snapshot

    def unload_models(self, ollama_client) -> bool:
        """
        Unload all currently-loaded Ollama models to free VRAM.
        Sends keep_alive=0 for each model found via /api/ps.
        """
        loaded = self._list_loaded_models_internal(ollama_client)
        if not loaded:
            print("[Fairness] No models currently loaded in Ollama VRAM.")
            return True

        print(f"[Fairness] Unloading {len(loaded)} model(s) from VRAM: {loaded}")
        for model_name in loaded:
            try:
                ollama_client.unload_model(model_name)
                print(f"[Fairness]   Unloaded: {model_name}")
            except Exception as e:
                print(f"[Fairness]   Warning: failed to unload {model_name}: {e}")
        return True

    def warmup_model(self, ollama_client) -> Dict[str, Any]:
        """
        Send a trivial prompt to force model loading before timed questions begin.
        Returns metadata about the warmup (load time, response time, etc.).
        """
        cfg = self._config.get("warmup", {})
        if not cfg.get("enabled", True):
            meta = {"skipped": True, "reason": "warmup disabled in config"}
            self._warmup_metadata = meta
            return meta

        prompt = cfg.get("warmup_prompt", "What is 2+2?")
        print(f"[Fairness] Warming up model '{ollama_client.model}' with prompt: '{prompt}'")
        start = time.time()
        response = ollama_client.query_llm(prompt)
        elapsed = time.time() - start

        load_duration = 0.0
        if response.ollama_metrics:
            load_duration = response.ollama_metrics.get("load_duration_s", 0.0)

        meta = {
            "warmup_prompt": prompt,
            "warmup_response_time_s": round(elapsed, 3),
            "model_load_duration_s": round(load_duration, 3),
            "success": response.success,
            "warmup_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self._warmup_metadata = meta
        print(
            f"[Fairness] Warmup complete. "
            f"Load: {load_duration:.2f}s, Total: {elapsed:.2f}s"
        )
        return meta

    def wait_for_cooldown(self, context: str = "between_models") -> Dict[str, Any]:
        """
        Wait for GPU temperature to drop below threshold (or max wait exceeded).
        Also enforces a minimum fixed wait from config.

        Args:
            context: "between_models" or "between_questions"
        """
        cfg = self._config.get("cooldown", {})

        if context == "between_questions":
            min_wait = cfg.get("between_questions_seconds", 0)
        else:
            min_wait = cfg.get("between_models_seconds", 60)

        temp_threshold = cfg.get("gpu_temp_threshold_c", 55)
        max_temp_wait = cfg.get("gpu_temp_wait_max_seconds", 300)

        start_temp = self._read_gpu_temp()
        start_time = time.time()

        print(
            f"[Fairness] Cooldown ({context}): "
            f"min wait={min_wait}s, GPU threshold={temp_threshold}°C"
        )
        if start_temp is not None:
            print(f"[Fairness] GPU temp at start: {start_temp:.1f}°C")

        # Enforce minimum fixed wait
        if min_wait > 0:
            time.sleep(min_wait)

        # Then poll until GPU temp is below threshold or max wait exceeded
        waited = time.time() - start_time
        while waited < max_temp_wait:
            current_temp = self._read_gpu_temp()
            if current_temp is None or current_temp <= temp_threshold:
                break
            print(
                f"[Fairness] GPU still warm ({current_temp:.1f}°C > {temp_threshold}°C), "
                f"waiting... ({waited:.0f}s elapsed)"
            )
            time.sleep(5)
            waited = time.time() - start_time

        end_temp = self._read_gpu_temp()
        total_wait = time.time() - start_time

        meta = {
            "context": context,
            "start_gpu_temp_c": round(start_temp, 1) if start_temp is not None else None,
            "end_gpu_temp_c": round(end_temp, 1) if end_temp is not None else None,
            "total_wait_s": round(total_wait, 1),
            "cooldown_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self._cooldown_metadata = meta
        print(
            f"[Fairness] Cooldown done. "
            f"End temp: {end_temp:.1f}°C, waited {total_wait:.1f}s"
            if end_temp is not None
            else f"[Fairness] Cooldown done. Waited {total_wait:.1f}s"
        )
        return meta

    def get_fairness_snapshot(self) -> Dict[str, Any]:
        """Return a full snapshot of fairness settings and runtime metadata for embedding in results."""
        return {
            "fairness_version": self._config.get("fairness_version", "1.0"),
            "ollama_parameters": dict(self._config.get("ollama_parameters", {})),
            "model_overrides_config": self._config.get("model_overrides", {}),
            "cooldown_config": self._config.get("cooldown", {}),
            "warmup_config": self._config.get("warmup", {}),
            "system_validation_config": self._config.get("system_validation", {}),
            "system_validation_result": self._validation_metadata,
            "warmup_result": self._warmup_metadata,
            "cooldown_result": self._cooldown_metadata,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _list_loaded_models_internal(self, ollama_client=None) -> List[str]:
        """Query Ollama /api/ps to find currently loaded models."""
        try:
            import requests
            if ollama_client is not None:
                base_url = ollama_client.base_url
            else:
                base_url = "http://localhost:11434"
            resp = requests.get(f"{base_url}/api/ps", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception:
            pass
        return []
