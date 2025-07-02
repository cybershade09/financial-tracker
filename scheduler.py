import schedule
import time
from datetime import datetime, timedelta
from tools import sql_read,sql_write

def end_of_month_job():
    if (datetime.today()+ timedelta(days=1)).day == 1:
        



schedule.every().day.at("23:59").do(end_of_month_job)

while True:
    schedule.run_pending()
    time.sleep(60)  
