import uvicorn
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("=" * 50)
    print("🎮 Dota 2 Winline Analyzer запускается...")
    print("📊 Открой браузер: http://localhost:8000")
    print("=" * 50)
    
    uvicorn.run(
        "src.web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
