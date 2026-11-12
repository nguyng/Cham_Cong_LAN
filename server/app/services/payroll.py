from collections import defaultdict
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import (
    AttendanceRecord,
    Employee,
    LeaveRequest,
    LeaveType,
    RequestStatus,
    ShiftAssignment,
)

MONEY = Decimal("0.01")
MONTH_LABELS = (
    "T01",
    "T02",
    "T03",
    "T04",
    "T05",
    "T06",
    "T07",
    "T08",
    "T09",
    "T10",
    "T11",
    "T12",
)


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _number(value: Decimal) -> float:
    return float(_money(value))


def _month_keys(year: int, month: int | None, last_month: int) -> list[tuple[int, int]]:
    if month is not None:
        return [(year, month)] if month <= last_month else []
    return [(year, current_month) for current_month in range(1, last_month + 1)]


def payroll_report(
    db: Session,
    *,
    year: int,
    month: int | None = None,
    department_id: int | None = None,
    employee_id: int | None = None,
    today: date | None = None,
) -> dict:
    """Calculate actual payroll from assignments, attendance and paid leave.

    Base salary is prorated per month by payable assigned days. A monthly attendance
    bonus is awarded when every assigned day is covered by attendance or paid leave,
    with no late arrival, early departure or suspicious attendance in that month.
    Approved overtime is paid from the scheduled minute rate and employee multiplier.
    """

    today = today or datetime.now(ZoneInfo(get_settings().work_timezone)).date()
    if year > today.year:
        raise ValueError("Không thể tính lương cho năm trong tương lai")
    year_start = date(year, 1, 1)
    year_end = min(date(year, 12, 31), today) if year == today.year else date(year, 12, 31)
    if month is not None and not 1 <= month <= 12:
        raise ValueError("Tháng phải nằm trong khoảng từ 1 đến 12")
    if year == today.year and month is not None and month > today.month:
        raise ValueError("Không thể tính lương cho tháng trong tương lai")

    employee_query = select(Employee).where(
        or_(Employee.hire_date.is_(None), Employee.hire_date <= year_end)
    )
    if department_id is not None:
        employee_query = employee_query.where(Employee.department_id == department_id)
    if employee_id is not None:
        employee_query = employee_query.where(Employee.id == employee_id)
    employees = db.scalars(employee_query.order_by(Employee.employee_code)).all()
    employee_ids = [employee.id for employee in employees]

    empty_chart = [
        {
            "month": index,
            "label": label,
            "base": 0.0,
            "bonus": 0.0,
            "overtime": 0.0,
            "total": 0.0,
        }
        for index, label in enumerate(MONTH_LABELS, start=1)
    ]
    if not employee_ids:
        return {
            "summary": {
                "total_payroll": 0.0,
                "total_base": 0.0,
                "total_bonus": 0.0,
                "total_overtime": 0.0,
                "bonus_recipients": 0,
                "employee_count": 0,
            },
            "monthly_chart": empty_chart,
            "top_earners": [],
            "items": [],
        }

    assignments: dict[tuple[int, int], set[date]] = defaultdict(set)
    scheduled_minutes: dict[tuple[int, int], int] = defaultdict(int)
    assignment_query = select(ShiftAssignment).where(
        ShiftAssignment.employee_id.in_(employee_ids),
        ShiftAssignment.work_date.between(year_start, year_end),
    )
    for assignment in db.scalars(assignment_query):
        key = (assignment.employee_id, assignment.work_date.month)
        assignments[key].add(assignment.work_date)
        start_minute = assignment.shift.start_time.hour * 60 + assignment.shift.start_time.minute
        end_minute = assignment.shift.end_time.hour * 60 + assignment.shift.end_time.minute
        duration = (end_minute - start_minute) % (24 * 60)
        duration = duration or 24 * 60
        scheduled_minutes[key] += max(0, duration - assignment.shift.break_minutes)

    attendance_dates: dict[tuple[int, int], set[date]] = defaultdict(set)
    attendance_stats: dict[tuple[int, int], dict[str, int]] = defaultdict(
        lambda: {
            "late": 0,
            "early": 0,
            "suspicious": 0,
            "minutes": 0,
            "overtime_minutes": 0,
        }
    )
    attendance_query = select(AttendanceRecord).where(
        AttendanceRecord.employee_id.in_(employee_ids),
        AttendanceRecord.work_date.between(year_start, year_end),
    )
    for record in db.scalars(attendance_query):
        key = (record.employee_id, record.work_date.month)
        attendance_dates[key].add(record.work_date)
        attendance_stats[key]["late"] += int(record.late_minutes > 0)
        attendance_stats[key]["early"] += int(record.early_leave_minutes > 0)
        attendance_stats[key]["suspicious"] += int(record.suspicious)
        attendance_stats[key]["minutes"] += record.worked_minutes
        if record.overtime_status == "APPROVED":
            attendance_stats[key]["overtime_minutes"] += record.approved_overtime_minutes

    paid_leave_dates: dict[tuple[int, int], set[date]] = defaultdict(set)
    leave_query = (
        select(LeaveRequest)
        .join(LeaveType, LeaveRequest.leave_type_id == LeaveType.id)
        .where(
            LeaveRequest.employee_id.in_(employee_ids),
            LeaveRequest.status == RequestStatus.APPROVED,
            LeaveType.paid.is_(True),
            LeaveRequest.start_date <= year_end,
            LeaveRequest.end_date >= year_start,
        )
    )
    for leave in db.scalars(leave_query):
        for current_month in range(1, 13):
            key = (leave.employee_id, current_month)
            paid_leave_dates[key].update(
                work_date
                for work_date in assignments[key]
                if leave.start_date <= work_date <= leave.end_date
            )

    last_month = year_end.month
    selected_months = _month_keys(year, month, last_month)
    monthly_totals = {
        current_month: {"base": Decimal(0), "bonus": Decimal(0), "overtime": Decimal(0)}
        for current_month in range(1, 13)
    }
    employee_monthly: dict[int, dict[int, dict]] = defaultdict(dict)

    for employee in employees:
        monthly_salary = Decimal(employee.base_salary or 0)
        monthly_bonus = Decimal(employee.attendance_bonus or 0)
        overtime_multiplier = Decimal(employee.overtime_multiplier or Decimal("1.50"))
        for current_month in range(1, last_month + 1):
            key = (employee.id, current_month)
            scheduled_dates = assignments[key]
            attended_dates = attendance_dates[key]
            attended_assigned = scheduled_dates & attended_dates
            paid_dates = (paid_leave_dates[key] & scheduled_dates) - attended_assigned
            scheduled_days = len(scheduled_dates)
            payable_days = min(scheduled_days, len(attended_assigned) + len(paid_dates))
            stats = attendance_stats[key]
            base_earned = (
                monthly_salary * Decimal(payable_days) / Decimal(scheduled_days)
                if scheduled_days
                else Decimal(0)
            )
            bonus_eligible = bool(
                scheduled_days
                and payable_days == scheduled_days
                and stats["late"] == 0
                and stats["early"] == 0
                and stats["suspicious"] == 0
            )
            bonus_earned = monthly_bonus if bonus_eligible else Decimal(0)
            overtime_earned = (
                monthly_salary
                * Decimal(stats["overtime_minutes"])
                * overtime_multiplier
                / Decimal(scheduled_minutes[key])
                if scheduled_minutes[key]
                else Decimal(0)
            )
            base_earned = _money(base_earned)
            bonus_earned = _money(bonus_earned)
            overtime_earned = _money(overtime_earned)
            employee_monthly[employee.id][current_month] = {
                "scheduled_days": scheduled_days,
                "work_days": len(attended_dates),
                "paid_leave_days": len(paid_dates),
                "absence_days": max(0, scheduled_days - payable_days),
                "worked_minutes": stats["minutes"],
                "late_count": stats["late"],
                "early_count": stats["early"],
                "suspicious_count": stats["suspicious"],
                "base_earned": base_earned,
                "bonus_earned": bonus_earned,
                "overtime_minutes": stats["overtime_minutes"],
                "overtime_earned": overtime_earned,
                "bonus_eligible": bonus_eligible,
            }
            monthly_totals[current_month]["base"] += base_earned
            monthly_totals[current_month]["bonus"] += bonus_earned
            monthly_totals[current_month]["overtime"] += overtime_earned

    rows = []
    for employee in employees:
        periods = [employee_monthly[employee.id][key[1]] for key in selected_months]
        scheduled_days = sum(period["scheduled_days"] for period in periods)
        work_days = sum(period["work_days"] for period in periods)
        paid_leave_days = sum(period["paid_leave_days"] for period in periods)
        absence_days = sum(period["absence_days"] for period in periods)
        base_earned = sum((period["base_earned"] for period in periods), Decimal(0))
        bonus_earned = sum((period["bonus_earned"] for period in periods), Decimal(0))
        overtime_earned = sum((period["overtime_earned"] for period in periods), Decimal(0))
        bonus_months = sum(int(period["bonus_eligible"]) for period in periods)
        eligible_months = sum(int(period["scheduled_days"] > 0) for period in periods)
        attendance_rate = (
            round(100 * (scheduled_days - absence_days) / scheduled_days, 1)
            if scheduled_days
            else 0.0
        )
        rows.append(
            {
                "employee_id": employee.id,
                "employee_code": employee.employee_code,
                "full_name": employee.full_name,
                "department_name": (
                    employee.department.name if employee.department else "Chưa phân phòng"
                ),
                "base_salary": _number(Decimal(employee.base_salary or 0)),
                "attendance_bonus": _number(Decimal(employee.attendance_bonus or 0)),
                "overtime_multiplier": float(employee.overtime_multiplier or Decimal("1.50")),
                "scheduled_days": scheduled_days,
                "work_days": work_days,
                "paid_leave_days": paid_leave_days,
                "absence_days": absence_days,
                "worked_hours": round(
                    sum(period["worked_minutes"] for period in periods) / 60, 2
                ),
                "late_count": sum(period["late_count"] for period in periods),
                "early_count": sum(period["early_count"] for period in periods),
                "base_earned": _number(base_earned),
                "bonus_earned": _number(bonus_earned),
                "approved_overtime_hours": round(
                    sum(period["overtime_minutes"] for period in periods) / 60, 2
                ),
                "overtime_earned": _number(overtime_earned),
                "total_salary": _number(base_earned + bonus_earned + overtime_earned),
                "attendance_rate": attendance_rate,
                "bonus_months": bonus_months,
                "bonus_status": (
                    "Chưa có lịch"
                    if not eligible_months
                    else (
                        "Đạt thưởng"
                        if month is not None and bonus_months
                        else (
                            "Không đạt"
                            if month is not None
                            else f"{bonus_months}/{eligible_months} tháng"
                        )
                    )
                ),
            }
        )

    total_base = sum((Decimal(str(row["base_earned"])) for row in rows), Decimal(0))
    total_bonus = sum((Decimal(str(row["bonus_earned"])) for row in rows), Decimal(0))
    total_overtime = sum((Decimal(str(row["overtime_earned"])) for row in rows), Decimal(0))
    monthly_chart = []
    for current_month, label in enumerate(MONTH_LABELS, start=1):
        base = monthly_totals[current_month]["base"]
        bonus = monthly_totals[current_month]["bonus"]
        overtime = monthly_totals[current_month]["overtime"]
        monthly_chart.append(
            {
                "month": current_month,
                "label": label,
                "base": _number(base),
                "bonus": _number(bonus),
                "overtime": _number(overtime),
                "total": _number(base + bonus + overtime),
            }
        )
    top_earners = [
        {
            "label": row["full_name"].split()[-1],
            "employee_code": row["employee_code"],
            "total": row["total_salary"],
            "bonus": row["bonus_earned"],
        }
        for row in sorted(rows, key=lambda item: item["total_salary"], reverse=True)[:8]
    ]
    return {
        "summary": {
            "total_payroll": _number(total_base + total_bonus + total_overtime),
            "total_overtime": _number(total_overtime),
            "total_base": _number(total_base),
            "total_bonus": _number(total_bonus),
            "bonus_recipients": sum(int(row["bonus_earned"] > 0) for row in rows),
            "employee_count": len(rows),
        },
        "monthly_chart": monthly_chart,
        "top_earners": top_earners,
        "items": rows,
    }
