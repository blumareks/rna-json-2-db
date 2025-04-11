from flask import Flask, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import requests
import datetime
import csv
import io

from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Retrieve the database configuration from the environment
URI = os.getenv("URL")
RNA_URL = os.getenv("RNA_DATA_URL")
app = Flask(__name__)

# prepare SQLAlchemy DB
# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = URI; #'postgresql://username:password@localhost:5432/alerts_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define database models
class PerformanceMetricsIndex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index_no = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.String(12), nullable=False)  # YYYYMMDDHHMM

with app.app_context():
    db.create_all()

class PerformanceMetricsData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index_no = db.Column(db.Integer, nullable=True)
    device_id = db.Column(db.String(50), nullable=False)
    device_name = db.Column(db.String(100), nullable=False)
    object_id = db.Column(db.String(50), nullable=False)
    object_name = db.Column(db.String(255), nullable=False)
    loss_percentage = db.Column(db.Float, nullable=True)
    jitter = db.Column(db.Float, nullable=True)
    latency = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.String(12), nullable=False)  # YYYYMMDDHHMM

with app.app_context():
    db.create_all()

def get_next_index():
    """Retrieve and update the index counter."""
    index_record = PerformanceMetricsIndex.query.order_by(PerformanceMetricsIndex.id.desc()).first()
    if index_record:
        new_index = index_record.index_no + 1 if index_record.index_no < 20000 else 1
    else:
        new_index = 1

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    
    new_index_record = PerformanceMetricsIndex(index_no=new_index, timestamp=timestamp)
    db.session.add(new_index_record)
    db.session.commit()
    
    return new_index

def fetch_performance_metrics():
    """Fetch performance metrics from the RNI API."""
    url = RNA_URL
    response = requests.get(url, verify=False)  # SSL verification disabled for local testing
    if response.status_code == 200:
        return response.json()
    else:
        return None

@app.route('/data/pullperformancemetrics', methods=['GET'])
def pull_performance_metrics():
    print("pulling performance metrics from RNA - index no:")
    index_no = get_next_index()
    print(index_no)


    # Clear previous entries for this index
    PerformanceMetricsData.query.filter_by(index_no=index_no).delete()
    print("cleared prvious performance metrics for this index")
    
    metrics_data = fetch_performance_metrics()
    if not metrics_data:
        print("Failed to fetch performance metrics")
        return jsonify({'error': 'Failed to fetch performance metrics'}), 500

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")

    try:
        devices = metrics_data.get("result", {}).get("devices", [])
        for device in devices:
            device_id = device.get("id")
            device_name = device.get("name")

            for obj in device.get("objects", []):
                object_id = obj.get("id")
                object_name = obj.get("name")

                loss_percentage = None
                jitter = None
                latency = None

                for indicator in obj.get("indicators", []):
                    if indicator.get("name") == "loss_percentage":
                        loss_percentage = indicator.get("value")
                    elif indicator.get("name") == "jitter":
                        jitter = indicator.get("value")
                    elif indicator.get("name") == "latency":
                        latency = indicator.get("value")

                metric_entry = PerformanceMetricsData(
                    index_no=index_no,
                    device_id=device_id,
                    device_name=device_name,
                    object_id=object_id,
                    object_name=object_name,
                    loss_percentage=loss_percentage,
                    jitter=jitter,
                    latency=latency,
                    timestamp=timestamp
                )
                db.session.add(metric_entry)

        db.session.commit()
        return jsonify({'message': 'Performance metrics updated successfully', 'index': index_no}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/data/exportcsv/<device_id>', methods=['GET'])
def export_performance_metrics_csv(device_id):
    """Exports the latest 1000 records for a device in CSV format."""
    records = (PerformanceMetricsData.query
               .filter_by(device_id=device_id)
               .order_by(PerformanceMetricsData.id.desc())
               .limit(20000)
               .all())

    if not records:
        return jsonify({'error': 'No records found for the given device_id'}), 404

    # Create CSV in-memory
    output = io.StringIO()
    csv_writer = csv.writer(output)
    
    # Write header
    csv_writer.writerow(["Index", "Device ID", "Device Name", "Object ID", "Object Name", 
                         "Loss Percentage", "Jitter", "Latency", "Timestamp"])
    
    # Write data
    for record in records:
        csv_writer.writerow([
            record.index_no,
            record.device_id,
            record.device_name,
            record.object_id,
            record.object_name,
            record.loss_percentage,
            record.jitter,
            record.latency,
            record.timestamp
        ])
    
    output.seek(0)

    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=performance_metrics_{device_id}.csv"})

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
