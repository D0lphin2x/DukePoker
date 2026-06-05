import os
import time
from collections import defaultdict, deque

from flask import Flask, abort, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("FLASK_COOKIE_SECURE", "true").lower() == "true",
)

trusted_proxy_hops = int(os.getenv("TRUSTED_PROXY_HOPS", "0"))
if trusted_proxy_hops > 0:
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=trusted_proxy_hops,
        x_proto=trusted_proxy_hops,
        x_host=trusted_proxy_hops,
        x_port=trusted_proxy_hops,
    )

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1200"))
TRUST_CF_CONNECTING_IP = os.getenv("TRUST_CF_CONNECTING_IP", "false").lower() == "true"
ALLOWED_HOSTS = {
    host.strip().lower()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
}
_request_log = defaultdict(deque)


def _client_key():
    if TRUST_CF_CONNECTING_IP:
        return request.headers.get("CF-Connecting-IP") or request.remote_addr or "unknown"
    return request.remote_addr or "unknown"


def _rate_limited(key, now):
    window = _request_log[key]
    oldest_allowed = now - 3600
    while window and window[0] < oldest_allowed:
        window.popleft()

    per_minute_count = sum(1 for timestamp in window if timestamp >= now - 60)
    if per_minute_count >= RATE_LIMIT_PER_MINUTE or len(window) >= RATE_LIMIT_PER_HOUR:
        return True

    window.append(now)
    if len(_request_log) > 10000:
        for stored_key in list(_request_log.keys())[:1000]:
            if not _request_log[stored_key] or _request_log[stored_key][-1] < oldest_allowed:
                _request_log.pop(stored_key, None)
    return False


@app.before_request
def enforce_request_limits():
    if ALLOWED_HOSTS:
        hostname = (request.host or "").split(":", 1)[0].lower()
        if hostname not in ALLOWED_HOSTS:
            abort(400)

    if _rate_limited(_client_key(), time.time()):
        abort(429)


@app.after_request
def set_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self' https://docs.google.com https://duke.campusgroups.com; "
        "frame-ancestors 'none'",
    )
    if request.is_secure or os.getenv("FORCE_HSTS", "false").lower() == "true":
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    return response

# Move announcement data to a top-level variable so it can be reused on the index page
ANNOUNCEMENTS = [
    {
        "title": "Spring Poker and BOBA",
        "date": "October 20, 2025: 7 PM - 11 PM",
        "description": "Join us for the first Poker Event after Spring break! $10 buy ins, and BOBA for all participants!",
        "image": "static/images/boba.jpeg",  # Example image path
        "link": ""
    },
    {
        "title": "Poker X Lambdas",
        "date": "November 7, 2025: 7 PM - 10 PM",
        "description": "Join us in our collab wtih Duke Lambdas at Wilkinson 126! $20 buy ins, rebuys allowed until first break, come and have fun!",
        "image": "static/images/dukelambdas.png",  # Example image path
        "link": "https://docs.google.com/forms/d/e/1FAIpQLSdtd8viMQl1OMKYHWBUd6KOTNrDqJlNScn5OZNCCiOc5y9QiA/viewform"
    },
    {
        "title": "First Poker Night",
        "date": "October 3, 2025: 7 PM - 11 PM",
        "description": "Join us for the first poker event of the year! Students of all experience levels can join.",
        "image": "static/images/R.jpeg",  # Example image path
        "link": "https://docs.google.com/forms/d/e/1FAIpQLSeT9wWF3pjq6ej19edwfZyiIGXpWfx7WK1l0OZmq6R23cxgVw/viewform"
    },
]

@app.route('/')
def home():
    # replicate sponsors list used on the sponsors page so logos show on the home page
    sponsors = [
        {"name": "Kalshi", "logo": "images/kalshi.png", "description": "Kalshi description..."},
        # add more if needed
    ]
    return render_template('index.html', announcements=ANNOUNCEMENTS, sponsors=sponsors)

@app.route('/about')
def about():
    return render_template('about.html', announcements=ANNOUNCEMENTS)

@app.route('/team')
def team():
    # example team data (images should be placed under static/images/)
    team_members = [
        {"name": "Andrew Park", "role": "Co-President", "image": "images/andrewpark.png", "bio": "Major: Math & Computer Science 2028 Interests: Piano, College Football, Strategy games", "linkedin": "https://www.linkedin.com/in/andrewparkus"},
        {"name": "Jason Chen", "role": "Co-President", "image": "images/jasonchen.png", "bio": "Major: Economics Interests: Options Trading, Brawl Stars, Ginger and Soy", "linkedin": "https://www.linkedin.com/in/jason-chen-066115217"},
        {"name": "Jason Dong", "role": "Secretary", "image": "images/jasondong.png", "bio": "Major: Economics & Statistics Interests: Soccer, Tennis, EDM, Lifting", "linkedin": "https://www.linkedin.com/in/jdong06"},
        {"name": "Jiyu Hong", "role": "Treasurer", "image": "images/jiyuhong-team.png", "bio": "Major: Biology & English Interests: Running, Baking, Grocery Shopping", "linkedin": ""},
        {"name": "Jay Shin", "role": "Publicity & Outreach", "image": "images/jayshin.png", "bio": "Major: Statistics & Economics Interests: Volleyball, Languages", "linkedin": "https://www.linkedin.com/in/jay-shin-143853347"},
        {"name": "David Kim", "role": "Event Organizer", "image": "images/davidkim.png", "bio": "Major: Chemistry Interests: Singing, Fishing, Sleeping", "linkedin": ""},
        {"name": "William He", "role": "Tech Director", "image": "images/slowpoke.png", "bio": "Major: Music & Cultural Anthropology Interest: Food", "linkedin": "https://www.linkedin.com/in/williamhehe"},
    ]
    return render_template('team.html', announcements=ANNOUNCEMENTS, team_members=team_members)

@app.route('/announcements')
def announcements():
    # reuse top-level announcements variable
    return render_template('announcements.html', announcements=ANNOUNCEMENTS)

@app.route('/sponsors')
def sponsors():
    # Sponsor entries — store logo file names under static/images/
    sponsors = [
        {
            "name": "Kalshi",
            "logo": "images/kalshi.png",  # put static/images/kalshi.png in the repo
            "description": "Kalshi is a regulated event-contract marketplace that lets users take positions on real-world outcomes. Built with compliance in mind, Kalshi provides a transparent, CFTC-regulated platform where traders can express views on events ranging from economic indicators to major public events."
        },
        # Add more sponsors here:
        # {"name": "ACME Corp", "logo": "images/acme.png", "description": "Supporter and partner."},
    ]
    return render_template('sponsors.html', sponsors=sponsors, announcements=ANNOUNCEMENTS)

@app.route('/gallery')
def gallery():
    # Example gallery events with images (place images in static/images/)
    gallery_events = [
        {
            "title": "First Poker Night",
            "images": ["images/firstpoker5.png","images/firstpoker1.png", "images/firstpoker2.png","images/firstpoker3.png","images/firstpoker4.png",],
        },
    ]
    return render_template('gallery.html', gallery_events=gallery_events, announcements=ANNOUNCEMENTS)

@app.route('/join')
def join():
    return render_template('join.html', announcements=ANNOUNCEMENTS)

if __name__ == '__main__':
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
