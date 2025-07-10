from app import app, db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = inspector.get_columns('question')
    print('Columns in question table:')
    for col in columns:
        print(col['name']) 