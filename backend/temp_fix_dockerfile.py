with open("backend/Dockerfile", "r") as f:
    content = f.read()
    
content = content.replace('"--reload"', '"--workers", "4"')

with open("backend/Dockerfile", "w") as f:
    f.write(content)
