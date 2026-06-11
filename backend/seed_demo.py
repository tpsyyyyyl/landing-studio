"""Create the demo account with sample generations. Run: python -m backend.seed_demo"""

from .auth import DEMO_EMAIL, DEMO_PASSWORD, hash_password
from .database import Base, SessionLocal, engine
from .models import Generation, User

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name}</title>
<style>
  body {{ margin:0; font-family: system-ui, sans-serif; background:{bg}; color:{fg}; }}
  header {{ padding:80px 24px; text-align:center; }}
  h1 {{ font-size:3rem; margin:0 0 16px; }}
  p {{ font-size:1.2rem; opacity:.8; max-width:560px; margin:0 auto 32px; }}
  a.cta {{ display:inline-block; padding:14px 32px; border-radius:10px; background:{accent}; color:#fff; text-decoration:none; font-weight:600; }}
</style>
</head>
<body>
<header>
  <h1>{name}</h1>
  <p>{tagline}</p>
  <a class="cta" href="#">Get Started</a>
</header>
</body>
</html>"""

SAMPLES = [
    {
        "business_name": "Brew & Bloom Coffee",
        "description": "Specialty coffee shop with in-house roastery and a cozy plant-filled space.",
        "style": "light",
        "language": "English",
        "tagline": "Small-batch roasts and slow mornings in the heart of the city.",
        "bg": "#fafafa", "fg": "#171717", "accent": "#1d4ed8",
    },
    {
        "business_name": "PixelForge Studio",
        "description": "Indie game development studio crafting atmospheric 2D adventures.",
        "style": "dark",
        "language": "English",
        "tagline": "We forge worlds one pixel at a time.",
        "bg": "#0a0a14", "fg": "#f1f1f6", "accent": "#6366f1",
    },
    {
        "business_name": "SunnySide Yoga",
        "description": "Morning yoga classes and retreats for busy professionals.",
        "style": "vibrant",
        "language": "English",
        "tagline": "Start your day on the bright side.",
        "bg": "#fffaf5", "fg": "#1c1917", "accent": "#f97316",
    },
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == DEMO_EMAIL).first():
            print("Demo account already exists, nothing to do.")
            return
        user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
        db.add(user)
        db.flush()
        for s in SAMPLES:
            db.add(Generation(
                user_id=user.id,
                business_name=s["business_name"],
                description=s["description"],
                answers="",
                style=s["style"],
                language=s["language"],
                html=SAMPLE_HTML.format(
                    name=s["business_name"], tagline=s["tagline"],
                    bg=s["bg"], fg=s["fg"], accent=s["accent"],
                ),
            ))
        db.commit()
        print(f"Demo account created: {DEMO_EMAIL} with {len(SAMPLES)} sample generations.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
