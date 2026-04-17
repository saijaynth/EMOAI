import os
import re

components_dir = "frontend/components"
for file in os.listdir(components_dir):
    if file.endswith(".tsx"):
        path = os.path.join(components_dir, file)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        new_content = content
        
        # Replace text-border/60 -> text-slate-500 (fixing the contrast bug)
        new_content = new_content.replace("text-border/60", "text-slate-500")
        
        # Replace bg-border/5 -> bg-slate-50 (making bg slightly visible)
        new_content = new_content.replace("bg-border/5", "bg-slate-50")
        
        # Replace text-text -> text-ink (fixing invalid Tailwind class)
        new_content = re.sub(r'text-text/(\d+)', r'text-ink/\1', new_content)
        new_content = new_content.replace("text-text", "text-ink")
        
        # In QuizInput, bg-border/10 for inactive progressBar is barely visible. Make it bg-slate-200
        new_content = new_content.replace("bg-border/10", "bg-slate-200")
        
        if content != new_content:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed {file}")

# Do the same for app/page.tsx
app_dir = "frontend/app"
for file in os.listdir(app_dir):
    if file.endswith(".tsx"):
        path = os.path.join(app_dir, file)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        new_content = content
        new_content = new_content.replace("text-border/60", "text-slate-500")
        new_content = new_content.replace("bg-border/5", "bg-slate-50")
        new_content = re.sub(r'text-text/(\d+)', r'text-ink/\1', new_content)
        new_content = new_content.replace("text-text", "text-ink")
        new_content = new_content.replace("bg-border/10", "bg-slate-200")
        
        if content != new_content:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed {file}")

print("Running npm run build to check typescript validation.")
