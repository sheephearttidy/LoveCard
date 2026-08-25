from flask import Flask
import config
from model import db
from route import public, auth, admin

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

app.register_blueprint(public)
app.register_blueprint(auth)
app.register_blueprint(admin)




if __name__ == '__main__':
    app.run(debug=True,port=8000)