import re

path = "backend/app/main.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

pattern = r"@asynccontextmanager\nasync def lifespan\(app: FastAPI\):\n\s+# Initialize DB\n\s+Base.metadata.create_all\(bind=engine\)"

new_lifespan = """import sqlalchemy.exc

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB safely across multiple workers
    try:
        Base.metadata.create_all(bind=engine)
    except sqlalchemy.exc.OperationalError as e:
        if "already exists" not in str(e).lower():
            raise"""

text = re.sub(pattern, new_lifespan, text)

if '@app.get("/")' not in text:
    text += "\n@app.get('/')\ndef root_route():\n    return {'status': 'ok', 'message': 'Emo AI Backend is live'}\n"

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Done via regex")
