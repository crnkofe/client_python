import os
from typing import Callable, Iterable, Optional, Union

from .metrics_core import CounterMetricFamily, GaugeMetricFamily, Metric
from .registry import Collector, CollectorRegistry, REGISTRY

try:
    import resource

    _PAGESIZE = resource.getpagesize()
except ImportError:
    # Not Unix
    _PAGESIZE = 4096


METRICS_MAP = {
    "MemTotal": "mem_total",
    "MemFree": "mem_free",
    "MemAvailable": "mem_available",
    "SwapTotal": "swap_total",
    "SwapFree": "swap_free",
}


class SystemCollector(Collector):
    """Collector for system-level exports."""

    def __init__(self,
                 namespace: str = '',
                 _pid: Callable[[], Union[int, str]] = lambda: 'self',
                 proc: str = '/proc',
                 registry: Optional[CollectorRegistry] = REGISTRY):
        self._namespace = namespace
        self._proc = proc
        if namespace:
            self._prefix = namespace + '_system_'
        else:
            self._prefix = 'system_'
        self._ticks = 100.0
        try:
            self._ticks = os.sysconf('SC_CLK_TCK')
        except (ValueError, TypeError, AttributeError, OSError):
            pass

        # This is used to test if we can access /proc.
        self._btime = 0
        try:
            self._btime = self._boot_time()
        except OSError:
            pass
        if registry:
            registry.register(self)

    def _boot_time(self):
        with open(os.path.join(self._proc, 'stat'), 'rb') as stat:
            for line in stat:
                if line.startswith(b'btime '):
                    return float(line.split()[1])
        return 0

    def collect(self) -> Iterable[Metric]:
        if not self._btime:
            return []
        result = []
        with open('/proc/stat', 'r') as proc_stat:
            cpu_line = proc_stat.readline()
            cpu_data = cpu_line.split()
            # from man 5 proc
            # cpu 10132153 290696 3084719 46828483 16683 0 25195 0 175628 0
            # cpu0 1393280 32966 572056 13343292 6130 0 17875 0 23933 0
            # The amount of time, measured in units of USER_HZ (1/100ths of a second on most architectures, use sysconf(_SC_CLK_TCK) to obtain the right value), that the system ("cpu" line) or the specific CPU ("cpuN" line) spent in various states:
            #
            # user   (1) Time spent in user mode.
            # nice   (2) Time spent in user mode with low priority (nice).
            # system (3) Time spent in system mode.
            cpu_user = CounterMetricFamily(
                self._prefix + 'cpu_user_seconds_total',
                'Total user and system CPU time spent in seconds (user).',
                value=float(cpu_data[1]) / self._ticks,
            )
            cpu_system = CounterMetricFamily(
                self._prefix + 'cpu_system_seconds_total',
               'Total system CPU time spent in seconds (system).',
               value=float(cpu_data[3]) / self._ticks,
            )
            result.extend([cpu_user, cpu_system])

        # /proc/meminfo
        #   This  file reports statistics about memory usage on the system.  It is used by free(1) to report the amount of free and used memory (both physical and swap) on the system as well as the shared memory and buffers used by the kernel.  Each line of the file consists of a parameter name, followed by
        #   a colon, the value of the parameter, and an option unit of measurement (e.g., "kB").  The list below describes the parameter names and the format specifier required to read the field value.  Except as noted below, all of the fields have been present since at least Linux 2.6.0.  Some  fields  are
        #   displayed only if the kernel was configured with various options; those dependencies are noted in the list.
        #
        # MemTotal %lu
        # Total usable RAM (i.e., physical RAM minus a few reserved bits and the kernel binary code).
        #
        # MemFree %lu
        # The sum of LowFree+HighFree.
        #
        # MemAvailable %lu (since Linux 3.14)
        # An estimate of how much memory is available for starting new applications, without swapping.
        #
        # SwapTotal %lu
        # Total amount of swap space available.
        #
        # SwapFree %lu
        # Amount of swap space that is currently unused.
        with open('/proc/meminfo', 'r') as meminfo:
            for line in meminfo:
                # sample line looks like `MemTotal:       16089840 kB`
                parts = line.split()
                name = parts[0][:-1]
                if name not in METRICS_MAP:
                    continue
                metric = GaugeMetricFamily(
                    f"{self._prefix}{METRICS_MAP[name]}",
                    f'Total memory usage in {parts[2]} ({name})',
                    value=float(parts[1]),
                )
                result.append(metric)

        return result


SYSTEM_COLLECTOR = SystemCollector()
"""Default SystemCollector in default Registry REGISTRY."""
