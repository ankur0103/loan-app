from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime, timedelta
from calendar import monthrange  # Import to calculate the last day of the month
from constants import PERCENTAGE_DICT

app = Flask(__name__)

# Function to calculate the last day of the month
def last_day_of_month(date):
    year = date.year
    month = date.month
    # Get the last day of the current month
    last_day = monthrange(year, month)[1]
    return datetime(year, month, last_day)

# Function to calculate cash flow based on input data
def calculate_cash_flow(face_amount, spread, issue_date, first_payment_date, maturity_date, yield_value):
    # Convert dates to datetime objects
    issue_date = datetime.strptime(issue_date, '%Y-%m-%d')
    first_payment_date = datetime.strptime(first_payment_date, '%Y-%m-%d')
    maturity_date = datetime.strptime(maturity_date, '%Y-%m-%d')

    # Cash flow calculation parameters
    cash_flows = []

    # Generate cash flow until maturity date
    current_date = last_day_of_month(issue_date)
    principal = 0  # Only interest until the final maturity
    i = 0
    while current_date < maturity_date:
        if current_date == issue_date:
            interest = 0
        else:
            i += 1
            interest = (face_amount * (spread + (PERCENTAGE_DICT[i] if i <= 32 else PERCENTAGE_DICT[32]))) / 12
        discount_factor = 1 / (1 + yield_value/12) ** i
        present_value = (interest + principal) * discount_factor

        # Append data for this period
        cash_flows.append({
            "Pay Date": current_date.strftime('%Y-%m-%d'),
            "Principal": round(principal, 2),
            "Interest": round(interest, 2),
            "Discount Factor": round(discount_factor, 2),
            "Present Value": round(present_value, 2)
        })

        # Move to the next payment date, setting it to the last day of the next month
        next_month = current_date.month % 12 + 1
        next_year = current_date.year + (current_date.month // 12)
        current_date = last_day_of_month(datetime(next_year, next_month, 1))

    # Final payment at maturity date (with principal)
    interest = face_amount * (spread + (PERCENTAGE_DICT[i] if i <= 32 else PERCENTAGE_DICT[32])) / 12
    principal = face_amount
    discount_factor = 1 / (1 + yield_value/12) ** (i+1)
    present_value = (interest + principal) * discount_factor

    # Append final payment data
    cash_flows.append({
        "Pay Date": current_date.strftime('%Y-%m-%d'),
        "Principal": round(principal, 2),
        "Interest": round(interest, 2),
        "Discount Factor": round(discount_factor, 2),
        "Present Value": round(present_value, 2)
    })

    # Convert list of dictionaries to pandas DataFrame
    df = pd.DataFrame(cash_flows)

    # Calculate the price as the sum of present values divided by the face amount
    price = df['Present Value'].sum() / face_amount

    return price, df

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve form data
    face_amount = request.form['face_amount']
    spread = request.form['spread']
    issue_date = request.form['issue_date']
    first_payment_date = request.form['first_payment_date']
    maturity_date = request.form['maturity_date']
    yield_value = request.form['yield']

    # Calculate the cash flow using the form data
    price, cash_flow_df = calculate_cash_flow(float(face_amount), float(spread), issue_date,
                                              first_payment_date, maturity_date, float(yield_value))

    # Render the results in the result page
    return render_template('result.html', face_amount=face_amount, spread=spread,
                           issue_date=issue_date, first_payment_date=first_payment_date,
                           maturity_date=maturity_date, yield_value=yield_value,
                           price=price, tables=cash_flow_df.to_html(classes='data', header=True))

if __name__ == '__main__':
    app.run(debug=True)
