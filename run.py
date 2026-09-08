import uvicorn

if __name__ == "__main__":
    print("=======================================================")
    print("🕵️‍♂️⚖️  Starting The Fact Detective Agency Server...")
    print("🌐  Web Interface: http://127.0.0.1:8000")
    print("📖  API Docs:      http://127.0.0.1:8000/docs")
    print("=======================================================")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
