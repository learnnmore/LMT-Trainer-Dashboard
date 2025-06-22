from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from datetime import date as datetime_date  # Renamed to avoid conflict with field name

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    subjects = models.CharField(max_length=200)
    expected_daily_hours = models.FloatField()

    def __str__(self):
        return self.name

class Batch(models.Model):
    name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
    @property
    def status(self):
        if self.end_date and self.end_date < datetime.now().date():
            return "Completed"
        return "Ongoing"
    
    @property
    def days_taken(self):
        if self.end_date:
            return (self.end_date - self.start_date).days
        return (datetime.now().date() - self.start_date).days

class DailyClassLog(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.FloatField()

    def save(self, *args, **kwargs):
        # Convert date to datetime.date if it's a string
        if isinstance(self.date, str):
            try:
                year, month, day = map(int, self.date.split('-'))
                self.date = datetime_date(year, month, day)
            except (ValueError, TypeError):
                raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        
        # Ensure date is a datetime.date
        if not isinstance(self.date, datetime_date):
            raise ValueError("Date must be a datetime.date object.")
        
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        if end <= start:
            raise ValueError("End time must be after start time")
        self.duration = (end - start).seconds / 3600
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trainer.name} - {self.batch.name} - {self.date}"