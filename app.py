from flask import Flask, Response
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
import requests
import os
import sys
from urllib.parse import quote_plus

app = Flask(__name__)

LOGIN_ID = os.environ["LOGIN_ID"]
PASSWORD = os.environ["PASSWORD"]
REMOTE_URL = f"https://uppclmp.myxenius.com/thirdparty/api/gtOvrvw?login_id={quote_plus(LOGIN_ID)}&password={quote_plus(PASSWORD)}"
registry = CollectorRegistry()

errors_gauge = Gauge('uppcl_errors', 'Number of errors encountered')

@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()

    try:
        response = requests.get(REMOTE_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        data = data["resource"]
    except Exception as e:
        errors_gauge.inc()
        print(f"Error fetching or parsing data: {e}", file=sys.stderr)
        return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)

    fields = ['balance_amount', 'dg_balance_amount', 'dg_reading', 'grid_reading', 'dg_amt', 'grid_amt']
    for f in fields:
        try:
            val = float(data[f])
            gauge = Gauge(f'uppcl_{f}', f'{f.replace("_", " ").title()}', registry=registry)
            gauge.set(val)
        except Exception as e:
            errors_gauge.inc()
            print(f"Error processing field {f}: {e}", file=sys.stderr)
    return Response(generate_latest(REGISTRY) + generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

