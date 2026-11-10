import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    
    print("=" * 60)
    print("  🚗 RYDEON - VEHICLE RENTAL SYSTEM")
    print(f"  Running development server at: http://{host}:{port}/")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)
