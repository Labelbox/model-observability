
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

app = Flask(__name__)


secret = b'webhook_secret'

@app.route('/')
def health_check():
    return 'I'm alive!'

@app.route('/review', methods=['POST'])
def print_webhook_info():
    payload = request.data
    computed_signature = hmac.new(secret, msg=payload, digestmod=hashlib.sha1).hexdigest()
    if request.headers['X-Hub-Signature'] != 'sha1='+computed_signature:
        print('Error: computed_signature does not match signature provided in the headers')
        return 'Error', 500, 200
    #Write saved results - match external_id with a specific date. Or just use the upload date for the data_row in the payload
    result = json.loads(payload.decode('utf8'))


@app.route('/observe'):
    start_date = request_args.get('start_date')
    end_date = request_args.get('end_date', start_date)
    request_args.get('visualize', False)
    """
    This route will be used to see how the model is performing 
    - Optionally visualize some failure to see the cause
    """

    start_date = request_args.get('start_date')
    end_date = request_args.get('end_date', start_date)
    request_args.get('visualize', False)


    #Return performance statistics..



#This will run periodically
def sample_training_data(low_confidence):
    data = os.listdir('data_dir')
    

if __name__ == '__main__':
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(sample_training_data,'interval',minutes=60)
    sched.start()
    app.run(host = '0.0.0.0')


 

