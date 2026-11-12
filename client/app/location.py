import math

from PySide6.QtCore import (
    QCoreApplication,
    QLocationPermission,
    QObject,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtPositioning import QGeoPositionInfo, QGeoPositionInfoSource


class LocationRequest(QObject):
    """Read one position asynchronously without nesting the main UI event loop."""

    succeeded = Signal(dict)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, timeout_ms: int = 12_000, parent: QObject | None = None):
        super().__init__(parent)
        self.timeout_ms = timeout_ms
        self.source = None
        self._done = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._timeout)

    def start(self) -> None:
        application = QCoreApplication.instance()
        if application is None:
            self._fail("Ứng dụng chưa sẵn sàng để yêu cầu quyền vị trí.")
            return
        permission = QLocationPermission()
        permission.setAccuracy(QLocationPermission.Accuracy.Precise)
        permission.setAvailability(QLocationPermission.Availability.WhenInUse)
        status = application.checkPermission(permission)
        if status == Qt.PermissionStatus.Granted:
            self._start_source()
        elif status == Qt.PermissionStatus.Denied:
            self._fail(
                "Quyền vị trí đang bị từ chối. Hãy bật Location Services trong Windows Settings."
            )
        else:
            self.timer.start(min(self.timeout_ms, 10_000))
            application.requestPermission(permission, self._permission_result)

    def _permission_result(self, _permission) -> None:
        if self._done:
            return
        self.timer.stop()
        application = QCoreApplication.instance()
        permission = QLocationPermission()
        permission.setAccuracy(QLocationPermission.Accuracy.Precise)
        permission.setAvailability(QLocationPermission.Availability.WhenInUse)
        if application and application.checkPermission(permission) == Qt.PermissionStatus.Granted:
            self._start_source()
        else:
            self._fail(
                "Chưa được cấp quyền vị trí. Hãy cho phép ứng dụng truy cập vị trí rồi thử lại."
            )

    def _start_source(self) -> None:
        self.source = QGeoPositionInfoSource.createDefaultSource(self)
        if self.source is None:
            self._fail(
                "Máy không có nguồn GPS. Hãy bật Location Services của Windows rồi thử lại."
            )
            return
        self.source.setPreferredPositioningMethods(
            QGeoPositionInfoSource.PositioningMethod.AllPositioningMethods
        )
        self.source.positionUpdated.connect(self._position_updated)
        self.source.errorOccurred.connect(self._position_error)
        self.timer.start(self.timeout_ms)
        self.source.requestUpdate(self.timeout_ms)

    def _position_updated(self, info: QGeoPositionInfo) -> None:
        coordinate = info.coordinate()
        if not coordinate.isValid():
            return
        result = {
            "latitude": round(coordinate.latitude(), 7),
            "longitude": round(coordinate.longitude(), 7),
        }
        accuracy = info.attribute(QGeoPositionInfo.Attribute.HorizontalAccuracy)
        if isinstance(accuracy, (int, float)) and math.isfinite(accuracy) and accuracy >= 0:
            result["location_accuracy_meters"] = round(float(accuracy), 1)
        self._complete(result)

    def _position_error(self, value) -> None:
        if value == QGeoPositionInfoSource.Error.AccessError:
            self._fail(
                "Windows không cho phép truy cập vị trí. Hãy bật quyền vị trí cho ứng dụng desktop."
            )
        else:
            self._fail("Nguồn vị trí của Windows báo lỗi. Hãy kiểm tra Location Services.")

    def _timeout(self) -> None:
        self._fail(
            "Không lấy được tọa độ GPS trong thời gian cho phép. "
            "Hãy kiểm tra Location Services và thử lại."
        )

    def _complete(self, result: dict) -> None:
        if self._done:
            return
        self._done = True
        self.timer.stop()
        if self.source is not None:
            self.source.stopUpdates()
        self.succeeded.emit(result)
        self.finished.emit()

    def _fail(self, message: str) -> None:
        if self._done:
            return
        self._done = True
        self.timer.stop()
        if self.source is not None:
            self.source.stopUpdates()
        self.failed.emit(message)
        self.finished.emit()
