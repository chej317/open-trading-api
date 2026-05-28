import os
import re
from datetime import datetime

def export_today_chat():
    log_file = "log.md"
    if not os.path.exists(log_file):
        print(f"Error: {log_file} not found.")
        return

    now = datetime.now()
    # Handle multiple date formats that might appear in logs
    today_variants = [
        f"{now.year}년 {now.month}월 {now.day}일",
        f"{now.year}년 {now.month:02d}월 {now.day:02d}일",
        now.strftime("%Y-%m-%d")
    ]
    
    print(f"Searching for sessions from: {today_variants}")
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(log_file, "r", encoding="cp949") as f:
            content = f.read()

    # Split by USER blocks
    sessions = re.split(r"(?=## USER)", content)
    
    today_sessions = []
    for session in sessions:
        if any(variant in session for variant in today_variants):
            today_sessions.append(session)

    if not today_sessions:
        print("No sessions found for today in log.md.")
        return

    # Create daily filename
    today_filename = f"conversation_{now.strftime('%Y%m%d')}.md"
    
    # Check if we should append or overwrite
    # For daily files, we usually want to maintain one file per day with all sessions
    with open(today_filename, "w", encoding="utf-8") as f:
        f.write(f"# 🤖 Gemini CLI 대화 로그 - {now.strftime('%Y-%m-%d')}\n\n")
        f.write(f"*Last Updated: {now.strftime('%H:%M:%S')}*\n\n")
        
        for i, session in enumerate(today_sessions):
            # Clean up redundant session context
            cleaned = re.sub(r"<session_context>.*?</session_context>", "> [Session Context Omitted]", session, flags=re.DOTALL)
            # Format model responses for better readability
            cleaned = cleaned.replace("## MODEL ✨", "### 🤖 Gemini Response")
            cleaned = cleaned.replace("## USER 🧑‍💻", "### 👤 User Message")
            
            f.write(f"## 턴 {i+1}\n\n")
            f.write(cleaned.strip())
            f.write("\n\n---\n\n")

    print(f"Successfully exported today's chat to {today_filename}")

if __name__ == "__main__":
    export_today_chat()
