from dotenv import load_dotenv
load_dotenv()

from app.bot import create_app

if __name__ == "__main__":
    app = create_app()
    print("NutriScan bot is running...")
    app.run_polling()
