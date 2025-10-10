from flask import Flask, render_template

app = Flask(__name__)

# Move announcement data to a top-level variable so it can be reused on the index page
ANNOUNCEMENTS = [
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
        {"name": "Andrew Park", "role": "Co-President", "image": "images/andrewpark.png", "bio": "Major: Math & Computer Science 2028 Interests: Piano, College Football, Strategy games"},
        {"name": "Jason Chen", "role": "Co-President", "image": "images/jasonchen.png", "bio": "Major: Economics Interests: Options Trading, Brawl Stars, Ginger and Soy"},
        {"name": "Jason Dong", "role": "Secretary", "image": "images/jasondong.png", "bio": "Major: Economics & Statistics Interests: Soccer, Tennis, EDM, Lifting"},
        {"name": "Grace Kim", "role": "Treasurer", "image": "images/gracekim.png", "bio": "Major: Economics & Political Science Interests: Guitar, Making Music, Running"},
        {"name": "Jay Shin", "role": "Publicity & Outreach", "image": "images/jayshin.png", "bio": "Major: Statistics & Economics Interests: Volleyball, Languages"},
        {"name": "William He", "role": "Tech Director", "image": "images/slowpoke.png", "bio": "Major: Music & Cultural Anthropology Interest: Food"},
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
    app.run(debug=True)
