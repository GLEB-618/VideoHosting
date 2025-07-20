from app import app
from data.orm import SyncORM

if __name__ == "__main__":
    SyncORM.create_tables()
    app.run(debug=True)