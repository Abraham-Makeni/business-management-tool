import traceback
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal, Slot


T = TypeVar("T")


class _WorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class _Worker(QRunnable):
    def __init__(self, fn: Callable[[], T]) -> None:
        super().__init__()
        self.fn = fn
        self.signals = _WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.fn()
        except Exception:
            self.signals.failed.emit(traceback.format_exc())
            return
        self.signals.finished.emit(result)


@dataclass(frozen=True)
class JobHandle(Generic[T]):
    on_success: Callable[[T], None]
    on_error: Callable[[str], None]


class AsyncRunner:
    """Threadpool runner to keep UI responsive (no main-thread blocking)."""

    def __init__(self, pool: QThreadPool | None = None) -> None:
        self.pool = pool or QThreadPool.globalInstance()

    def run(self, fn: Callable[[], T], handle: JobHandle[T]) -> None:
        worker = _Worker(fn)
        # Ensure callbacks execute on the Qt/main thread.
        worker.signals.finished.connect(
            handle.on_success, Qt.ConnectionType.QueuedConnection
        )
        worker.signals.failed.connect(
            handle.on_error, Qt.ConnectionType.QueuedConnection
        )
        self.pool.start(worker)

