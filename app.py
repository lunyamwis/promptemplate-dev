from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crud.db'
db = SQLAlchemy(app)

# Define a simple model
class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def update(self, new_name):
        self.name = new_name
        db.session.commit()


@app.route('/')
def index():
    with app.app_context():
        prompts = Prompt.query.all()
    return render_template('index.html', prompts=prompts)

@app.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':
        with app.app_context():
            new_prompt = Prompt(name=request.form['name'])
            db.session.add(new_prompt)
            db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:prompt_id>')
def delete(prompt_id):
    with app.app_context():
        prompt = Prompt.query.get(prompt_id)
        db.session.delete(prompt)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:prompt_id>', methods=['GET', 'POST'])
def update_prompt(prompt_id):
    prompt = Prompt.query.get(prompt_id)

    if request.method == 'POST':
        new_name = request.form['name']
        prompt.update(new_name)
        return redirect(url_for('index'))

    return render_template('update.html', prompt=prompt)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
