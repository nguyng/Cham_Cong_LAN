from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
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
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)


class DepartmentIn(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    manager_employee_id: int | None = None


class PositionIn(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)


class EmployeeIn(BaseModel):
    employee_code: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str | None = None
    department_id: int | None = None
    position_id: int | None = None
    hire_date: date | None = None
    username: str = Field(min_length=3, max_length=80)
    temporary_password: str = Field(min_length=10, max_length=128)
    role: str = "EMPLOYEE"


class EmployeeUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str | None = None
    department_id: int | None = None
    position_id: int | None = None
    hire_date: date | None = None


class ShiftIn(BaseModel):
    code: str
    name: str
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
        if any(day < 0 or day > 6 for day in self.weekdays):
            raise ValueError("weekdays chỉ nhận giá trị 0..6")
        return self


class AttendanceAction(BaseModel):
    device_fingerprint: str | None = Field(default=None, max_length=128)
    idempotency_key: str = Field(min_length=8, max_length=100)


class AdjustmentIn(BaseModel):
    attendance_id: int
    proposed_check_in: datetime | None = None
    proposed_check_out: datetime | None = None
    reason: str = Field(min_length=5, max_length=2000)


class ReviewIn(BaseModel):
    approve: bool
    note: str = Field(min_length=2, max_length=2000)


class LeaveRequestIn(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc phải từ ngày bắt đầu trở đi")
        return self


class LeaveTypeIn(BaseModel):
    code: str
    name: str
    paid: bool = True
    deduct_balance: bool = True


class LeaveBalanceIn(BaseModel):
    employee_id: int
    leave_type_id: int
    year: int = Field(ge=2000, le=2200)
    allocated_days: Decimal = Field(ge=0, le=366)


class DeviceIn(BaseModel):
    fingerprint: str = Field(min_length=8, max_length=128)
    device_name: str = Field(min_length=1, max_length=160)


class RandomCheckResponse(BaseModel):
    challenge_token: str = Field(min_length=20)


class SettingIn(BaseModel):
    value: dict
    description: str | None = None
