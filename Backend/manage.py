import sys
from app import app
from seed_data import seed_database

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        seed_database()
    else:
        app.run(host='127.0.0.1', port=5000, debug=True)

if __name__ == '__main__':
    main()
