import os
import sqlalchemy

path = "backend/app/main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_lifespan = """@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB
    Base.metadata.create_all(bind=engine)

    recommender_service.load_catalog()
    feedback_store.load()
    user_store.load()
    yield"""

new_lifespan = """import sqlalchemy.exc
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB safely across multiple workers
    try:
        Base.metadata.create_all(bind=engine)
    except sqlalchemy.exc.OperationalError as e:
        if "already exists" not in str(e).lower():
            raise

    recommender_service.load_catalog()
    feedback_store.load()
    user_store.load()
    yield"""

content = content.replace(old_lifespan, new_lifespan)

if 'app.get("/")' not in content:
    content += """\n
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Emo AI Backend is running nicely!"}
"""

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to backend/app/main.py")
