from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

phone_numbers = [str(89138256851 + i) for i in range(1000)]

@app.route('/')
def index():
    return render_template('index.html', phone_numbers=phone_numbers)

@app.route('/number')
def number_details():
    number = request.args.get('number', '')
    return render_template('number.html', number=number)

@app.route('/search', methods=['GET'])
def search():
    number = request.args.get('phone_number', '')
    return redirect(url_for('number_details', number=number))

if __name__ == '__main__':
    app.run(debug=True)
