from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/announcements')
def announcements():
    # Change dictionary as required for photos and titles
    announcements = [
        {
            "title": "Annual Duke Poker Tournament",
            "date": "May 1, 2025",
            "description": "Join us for the biggest poker event of the year! Open to all Duke students.",
            "image": "static/images/tournament.jpg"  # Example image path
        },
        {
            "title": "Weekly Poker Night",
            "date": "Every Friday at 7 PM",
            "description": "Come and enjoy a casual poker night with fellow enthusiasts."
        },
        {
            "title": "Strategy Workshop",
            "date": "April 15, 2025",
            "description": "Learn advanced poker strategies from our experienced members.",
            "image": "static/images/workshop.jpg"  # Example image path
        }
    ]
    return render_template('announcements.html', announcements=announcements)

@app.route('/sponsors')
def sponsors():
    # Example sponsors data
    sponsors = [
        {
            "name": "PokerStars",
            "logo": "static/images/pokerstars_logo.png",
            "description": "PokerStars is the leading online poker platform, supporting our events and workshops."
        },
        {
            "name": "Duke Alumni Association",
            "logo": "static/images/duke_alumni_logo.png",
            "description": "The Duke Alumni Association generously sponsors our annual tournaments and networking events."
        },
        {
            "name": "Blue Devil Gaming",
            "logo": "static/images/blue_devil_gaming_logo.png",
            "description": "Blue Devil Gaming provides resources and support for our gaming nights and strategy workshops."
        }
    ]
    return render_template('sponsors.html', sponsors=sponsors)

@app.route('/gallery')
def gallery():
    # Change dictionary as required for photos and titles
    gallery_events = [
        {
            "title": "Annual Duke Poker Tournament",
            "images": [
                "static/images/tournament1.jpg",
                "static/images/tournament2.jpg",
                "static/images/tournament3.jpg"
            ]
        },
        {
            "title": "Weekly Poker Night",
            "images": [
                "static/images/pokernight1.jpg",
                "static/images/pokernight2.jpg"
            ]
        },
        {
            "title": "Strategy Workshop",
            "images": [
                "static/images/workshop1.jpg",
                "static/images/workshop2.jpg"
            ]
        }
    ]
    return render_template('gallery.html', gallery_events=gallery_events)

@app.route('/join')
def join():
    return render_template('join.html')

if __name__ == '__main__':
    app.run(debug=True)
