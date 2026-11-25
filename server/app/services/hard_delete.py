from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import Table

from app.database.session import Base
from app.models.entities import Employee, User


def hard_delete_record(db: Session, item):
    if isinstance(item, Employee):
        linked_user = db.scalar(select(User).where(User.employee_id == item.id))
        if linked_user:
            _delete_row(db, User.__table__, {"id": linked_user.id}, set())
    primary_key = {column.name: getattr(item, column.name) for column in item.__table__.primary_key}
    _delete_row(db, item.__table__, primary_key, set())


def _delete_row(db: Session, table: Table, key: dict, visiting: set):
    identity = (table.fullname, tuple(key[column.name] for column in table.primary_key))
    if identity in visiting:
        return
    visiting.add(identity)

    for child in Base.metadata.tables.values():
        for constraint in child.foreign_key_constraints:
            if constraint.referred_table is not table:
                continue
            elements = tuple(constraint.elements)
            conditions = [
                child.c[element.parent.name] == key[element.column.name] for element in elements
            ]
            local_columns = [element.parent.name for element in elements]
            if all(child.c[name].nullable for name in local_columns):
                db.execute(
                    update(child)
                    .where(*conditions)
                    .values({name: None for name in local_columns})
                )
                continue
            dependent_rows = db.execute(select(child).where(*conditions)).mappings().all()
            for row in dependent_rows:
                child_key = {
                    column.name: row[column.name] for column in child.primary_key
                }
                _delete_row(db, child, child_key, visiting)

    db.execute(delete(table).where(*[table.c[name] == value for name, value in key.items()]))
    visiting.remove(identity)
