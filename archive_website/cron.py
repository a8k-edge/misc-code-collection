from crontab import CronTab


def schedule_daily_job():
    cron = CronTab(user=True)
    job = cron.new(command='python archive.py')
    job.minute.on(0)
    job.hour.on(0)  # Runs at midnight
    cron.write()


schedule_daily_job()
