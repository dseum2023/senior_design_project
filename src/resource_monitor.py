"""
System Resource Monitor
Monitors CPU, RAM, GPU utilization during LLM inference via a background sampling thread.
"""

import threading
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ResourceMetrics:
    """Aggregated resource metrics from a monitoring session."""
    # RAM
    ram_peak_mb: float
    ram_avg_mb: float
    # CPU
    cpu_avg_percent: float
    cpu_peak_percent: float
    # GPU
    gpu_util_avg_percent: float
    gpu_util_peak_percent: float
    gpu_vram_peak_mb: float
    gpu_vram_avg_mb: float
    gpu_temp_avg_c: float
    gpu_temp_peak_c: float
    gpu_power_avg_w: float
    gpu_power_peak_w: float
    # Derived
    energy_estimate_wh: float
    monitoring_duration_s: float
    sample_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ResourceMonitor:
    """
    Monitors system resources (CPU, RAM, GPU) in a background thread.

    Usage:
        monitor = ResourceMonitor(sample_interval=0.5)
        with monitor:
            # ... run LLM query ...
        metrics = monitor.get_metrics()
    """

    def __init__(self, sample_interval: float = 0.5, gpu_index: int = 0):
        self._interval = sample_interval
        self._gpu_index = gpu_index
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._samples: List[Dict[str, float]] = []
        self._start_time: float = 0.0
        self._end_time: float = 0.0
        self._nvml_available = False
        self._gpu_handle = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def start(self):
        """Start background monitoring thread."""
        self._samples = []
        self._stop_event.clear()
        self._init_nvml()
        # Prime psutil cpu_percent so the first real sample isn't 0.0
        import psutil
        psutil.cpu_percent(interval=None)
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring and wait for thread to finish."""
        self._stop_event.set()
        self._end_time = time.time()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._shutdown_nvml()

    def _init_nvml(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            self._gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(self._gpu_index)
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
            self._nvml_available = False
            self._gpu_handle = None

    def _sample_loop(self):
        import psutil
        while not self._stop_event.is_set():
            sample = self._take_sample(psutil)
            self._samples.append(sample)
            self._stop_event.wait(self._interval)

    def _take_sample(self, psutil) -> Dict[str, float]:
        sample: Dict[str, float] = {}

        # RAM
        mem = psutil.virtual_memory()
        sample['ram_used_mb'] = mem.used / (1024 * 1024)

        # CPU (non-blocking instant reading)
        sample['cpu_percent'] = psutil.cpu_percent(interval=None)

        # GPU metrics via pynvml
        if self._nvml_available and self._gpu_handle:
            try:
                import pynvml
                util = pynvml.nvmlDeviceGetUtilizationRates(self._gpu_handle)
                sample['gpu_util_percent'] = float(util.gpu)

                mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._gpu_handle)
                sample['gpu_vram_used_mb'] = mem_info.used / (1024 * 1024)

                temp = pynvml.nvmlDeviceGetTemperature(
                    self._gpu_handle, pynvml.NVML_TEMPERATURE_GPU
                )
                sample['gpu_temp_c'] = float(temp)

                power = pynvml.nvmlDeviceGetPowerUsage(self._gpu_handle)  # milliwatts
                sample['gpu_power_w'] = power / 1000.0
            except Exception:
                sample['gpu_util_percent'] = 0.0
                sample['gpu_vram_used_mb'] = 0.0
                sample['gpu_temp_c'] = 0.0
                sample['gpu_power_w'] = 0.0
        else:
            sample['gpu_util_percent'] = 0.0
            sample['gpu_vram_used_mb'] = 0.0
            sample['gpu_temp_c'] = 0.0
            sample['gpu_power_w'] = 0.0

        return sample

    def get_metrics(self) -> Optional[ResourceMetrics]:
        """Compute aggregated metrics from collected samples."""
        if not self._samples:
            return None

        duration = self._end_time - self._start_time
        n = len(self._samples)

        ram_values = [s['ram_used_mb'] for s in self._samples]
        cpu_values = [s['cpu_percent'] for s in self._samples]
        gpu_util_values = [s['gpu_util_percent'] for s in self._samples]
        gpu_vram_values = [s['gpu_vram_used_mb'] for s in self._samples]
        gpu_temp_values = [s['gpu_temp_c'] for s in self._samples]
        gpu_power_values = [s['gpu_power_w'] for s in self._samples]

        avg_power = sum(gpu_power_values) / n
        energy_wh = avg_power * duration / 3600.0

        return ResourceMetrics(
            ram_peak_mb=round(max(ram_values), 1),
            ram_avg_mb=round(sum(ram_values) / n, 1),
            cpu_avg_percent=round(sum(cpu_values) / n, 1),
            cpu_peak_percent=round(max(cpu_values), 1),
            gpu_util_avg_percent=round(sum(gpu_util_values) / n, 1),
            gpu_util_peak_percent=round(max(gpu_util_values), 1),
            gpu_vram_peak_mb=round(max(gpu_vram_values), 1),
            gpu_vram_avg_mb=round(sum(gpu_vram_values) / n, 1),
            gpu_temp_avg_c=round(sum(gpu_temp_values) / n, 1),
            gpu_temp_peak_c=round(max(gpu_temp_values), 1),
            gpu_power_avg_w=round(avg_power, 1),
            gpu_power_peak_w=round(max(gpu_power_values), 1),
            energy_estimate_wh=round(energy_wh, 4),
            monitoring_duration_s=round(duration, 3),
            sample_count=n,
        )
