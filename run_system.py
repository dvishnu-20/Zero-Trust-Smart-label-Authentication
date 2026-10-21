import os
import sys
import time
import webbrowser
import subprocess

def main():
    print("=========================================================================")
    print(" Zero Trust Authentication for Smart Labels in Secure Supply Chains")
    print("=========================================================================")
    
    # Root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    # Step 1: Initialize Database and Seed Data
    print("\n[1/3] Initializing SQLite Database & Seeding Supply Chain Data...")
    from backend.seed import seed_database
    seed_database()

    # Step 2: Open Browser
    url = "http://localhost:8000"
    print(f"\n[2/3] Web Dashboard will be available at: {url}")
    
    def open_browser():
        time.sleep(1.5)
        print(f"Opening {url} in browser...")
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Step 3: Launch FastAPI Server via Uvicorn
    print("\n[3/3] Starting FastAPI Server on port 8000...")
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
