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
    return render_template('announcements.html')

@app.route('/sponsors')
def sponsors():
    return render_template('sponsors.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/join')
def join():
    return render_template('join.html')

if __name__ == '__main__':
    app.run(debug=True)
