import hashlib
from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Set flask app secret key for session
app.secret_key = "jaimenoel"


# configure the database URI or binds
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db = SQLAlchemy(app)



# creating the user model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


# creating the Ticker model
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text(), nullable=False)
    priority = db.Column(db.Enum('low', 'medium', 'high'), nullable=False)

    def __repr__(self):
        return '<Ticket %r>' % self.title


# Before all request route to check the user agent
#@app.before_request
#def before_request():
    # if the user-agent is not "Santanium X-12/25 pole-nord-special-browser", dont allow the request and show the WAF page
#    if request.headers.get('User-Agent') != "Santanium X-12/25 pole-nord-special-browser":
#        return render_template('waf.html')

# Check if the database exist and the table user exist too


# route for index
@app.route('/')
def index():
    return render_template('index.html')


# route for login user with a sqlite DB
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Hash the password.
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Check if the user exists in the database.
        user = User.query.filter_by(username=username).first()

        if user and user.password_hash == hashed_password:
            # The user exists and the password is correct.
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))

        else:
            # The user does not exist or the password is incorrect.
            return render_template("login.html", error="Invalid credentials.")

    return render_template("login.html")



# route for register user with a sqlite DB
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Hash the password.
        hashed_password = hashlib.sha256(password.encode()).hexdigest()



        # Check if the user exists in the database.
        user = User.query.filter_by(username=username).first()

        if user:
            # The user already exists.
            return render_template("register.html", error="User already exists.")

        # Create the user in the database.
        user = User(username=username, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()

        # Redirect the user to the login page.
        return redirect(url_for("login"))

    return render_template("register.html")


# route for dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Get all the tickets associated with the authenticated user.
    tickets = Ticket.query.filter_by(user_id=session["user_id"]).all()#.order_by(Ticket.priority).all()
    print(tickets)
    # Display the tickets in priority order.
    return render_template("dashboard.html", tickets=tickets)


# route for create ticket
@app.route("/create_ticket", methods=["GET", "POST"])
def create_ticket():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("create_ticket.html")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        priority = request.form["priority"]

        # Create a new ticket.
        ticket = Ticket(user_id=session["user_id"], title=title, description=description, priority=priority)
        db.session.add(ticket)
        db.session.commit()

        # Redirect the user to the dashboard.
        return redirect(url_for("dashboard"))


# route for view tickets
@app.route('/view_tickets', methods=['GET', 'POST'])
def view_tickets():
    # First verify that the user is logged-in
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Get all the tickets associated with the authenticated user.
    tickets = Ticket.query.filter_by(user_id=session["user_id"]).order_by(Ticket.priority).all()

    # Display the tickets in priority order.
    return render_template('view_tickets.html', tickets=tickets)


# route for edit ticket
@app.route('/edit_ticket/<ticket_id>', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    # is the user logged-in 
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # get the ticket from the database
    ticket = Ticket.query.filter_by(id=ticket_id).first()
    
    # if method is get, return edit page
    if request.method == "GET":
        return render_template('edit_ticket.html', ticket=ticket)

    if request.method == "POST":
        # modify the ticket with the new form
        ticket.title = request.form["title"]
        ticket.description = request.form["description"]
        ticket.priority = request.form["priority"]
        db.session.commit()

        return redirect(url_for("dashboard"))
    
    return render_template(url_for("dashboard"))



# route for delete ticket
@app.route('/delete_ticket', methods=['GET', 'POST'])
def delete_ticket():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # verify that the current user_id is associated with the targeted ticker
    ticket_id = request.args.get("ticket_id")
    if not ticket_id:
        return redirect(url_for("dashboard"))

    ticket = Ticket.query.filter_by(id=ticket_id).first()
    if ticket.user_id != session["user_id"]:
        return redirect(url_for("dashboard"))

    # delete the ticket
    db.session.delete(ticket)
    db.session.commit()

    # Can we notify the user that the deletion have been done
    return render_template("deleted.html")


# route for logout
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # remove the user_id from the session
    session.pop("user_id", None)

    # redirect the user to the login page
    return render_template('logout.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
