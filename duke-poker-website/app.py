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
            "title": "First Poker Night",
            "date": "October 3, 2025: 7 PM - 11 PM",
            "description": "Join us for the first poker event of the year! Students of all experience levels can join",
            "image": "static/images/R.jpeg"  # Example image path
        },
    ]
    return render_template('announcements.html', announcements=announcements)

@app.route('/sponsors')
def sponsors():
    # Example sponsors data
    sponsors = [ 
    ]
    return render_template('sponsors.html', sponsors=sponsors)

@app.route('/gallery')
def gallery():
    # Change dictionary as required for photos and titles
    gallery_events = [
    ]
    return render_template('gallery.html', gallery_events=gallery_events)

@app.route('/join')
def join():
    return render_template('join.html')

if __name__ == '__main__':
    app.run(debug=True)
