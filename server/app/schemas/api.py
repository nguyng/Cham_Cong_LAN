from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, model_validator

Code = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=160)]
DeviceName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=80)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=2000)]
ReviewNote = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=2000)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: Username
    password: str = Field(min_length=6, max_length=128)
    device_fingerprint: str | None = Field(default=None, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    role: str
    user_id: int
    employee_id: int | None


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class DepartmentIn(BaseModel):
    code: Code
    name: Name
    manager_employee_id: int | None = None


class PositionIn(BaseModel):
    code: Code
    name: Name


class EmployeeIn(BaseModel):
    employee_code: Code
    full_name: FullName
    email: EmailStr = Field(max_length=190)
    phone: Phone | None = None
    department_id: int | None = None
    position_id: int | None = None
    hire_date: date | None = None
    username: Username
    temporary_password: str = Field(min_length=10, max_length=128)
    role: Literal["ADMIN", "MANAGER", "EMPLOYEE"] = "EMPLOYEE"


class EmployeeUpdate(BaseModel):
    full_name: FullName
    email: EmailStr = Field(max_length=190)
    phone: Phone | None = None
    department_id: int | None = None
    position_id: int | None = None
    hire_date: date | None = None


class PayrollProfileIn(BaseModel):
    base_salary: Decimal = Field(ge=0, le=999_999_999_999)
    attendance_bonus: Decimal = Field(ge=0, le=999_999_999_999)
    overtime_multiplier: Decimal = Field(default=Decimal("1.50"), ge=1, le=5)


class ShiftIn(BaseModel):
    code: Code
    name: Name
    start_time: time
    end_time: time
    break_minutes: int = Field(default=0, ge=0, le=240)
    late_grace_minutes: int = Field(default=0, ge=0, le=120)
    early_grace_minutes: int = Field(default=0, ge=0, le=120)


class AssignmentIn(BaseModel):
    employee_id: int
    shift_id: int
    start_date: date
    end_date: date
    weekdays: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date phải từ start_date trở đi")
        if (self.end_date - self.start_date).days > 366:
            raise ValueError("Mỗi lần phân ca chỉ được tối đa 367 ngày")
        if not self.weekdays:
            raise ValueError("weekdays phải có ít nhất một ngày làm việc")
        if any(day < 0 or day > 6 for day in self.weekdays):
            raise ValueError("weekdays chỉ nhận giá trị 0..6")
        return self


class AttendanceAction(BaseModel):
    device_fingerprint: str = Field(min_length=8, max_length=128)
    idempotency_key: str = Field(min_length=8, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_accuracy_meters: float | None = Field(default=None, ge=0, le=100000)
    location_source: Literal["GPS", "LAN_IP_FALLBACK"] | None = None

    @model_validator(mode="after")
    def valid_location(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Kinh độ và vĩ độ phải được gửi cùng nhau")
        if self.location_accuracy_meters is not None and self.latitude is None:
            raise ValueError("Độ chính xác GPS yêu cầu kinh độ và vĩ độ")
        if self.location_source == "GPS" and self.latitude is None:
            raise ValueError("Nguồn GPS yêu cầu kinh độ và vĩ độ")
        if self.location_source == "LAN_IP_FALLBACK" and self.latitude is not None:
            raise ValueError("Nguồn IP nội bộ không được gửi kèm tọa độ GPS")
        return self


class AdjustmentIn(BaseModel):
    attendance_id: int
    proposed_check_in: datetime | None = None
    proposed_check_out: datetime | None = None
    reason: Reason

    @model_validator(mode="after")
    def valid_times(self):
        if not self.proposed_check_in and not self.proposed_check_out:
            raise ValueError("Phải đề xuất ít nhất giờ check-in hoặc check-out")
        if (
            self.proposed_check_in
            and self.proposed_check_out
            and self.proposed_check_out <= self.proposed_check_in
        ):
            raise ValueError("Giờ check-out phải sau giờ check-in")
        return self


class ReviewIn(BaseModel):
    approve: bool
    note: ReviewNote


class LeaveRequestIn(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: Reason

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc phải từ ngày bắt đầu trở đi")
        if (self.end_date - self.start_date).days > 366:
            raise ValueError("Một đơn nghỉ phép chỉ được kéo dài tối đa 367 ngày")
        return self


class LeaveTypeIn(BaseModel):
    code: Code
    name: Name
    paid: bool = True
    deduct_balance: bool = True


class LeaveBalanceIn(BaseModel):
    employee_id: int
    leave_type_id: int
    year: int = Field(ge=2000, le=2200)
    allocated_days: Decimal = Field(ge=0, le=366)


class DeviceIn(BaseModel):
    fingerprint: str = Field(min_length=8, max_length=128)
    device_name: DeviceName


class RandomCheckResponse(BaseModel):
    challenge_token: str = Field(min_length=20, max_length=512)


class SettingIn(BaseModel):
    value: dict
    description: str | None = None
