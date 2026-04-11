# FIX: Changed from relative import (from ..app import app) to absolute import (from app import app)
# Relative imports don't work when running main.py directly as a script
# This prevents ImportError: attempted relative import with no known parent package
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
