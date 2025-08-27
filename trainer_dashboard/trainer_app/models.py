from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    name = models.CharField(max_length=100)
    subjects = models.CharField(max_length=200)
    expected_daily_hours = models.FloatField()

    def __str__(self):
        return self.name

class Batch(models.Model):
    IT_COURSES = [
        ('python', 'Python'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('web_dev', 'Web Development'),
        ('data_science', 'Data Science'),
        ('ml', 'Machine Learning'),
        ('ai', 'Artificial Intelligence'),
        ('cloud', 'Cloud Computing'),
        ('cyber_sec', 'Cyber Security'),
        ('dbms', 'Database Management'),
    ]

    name = models.CharField(max_length=100)
    course = models.CharField(max_length=50, choices=IT_COURSES)  # dropdown
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    trainer = models.ForeignKey("Trainer", on_delete=models.CASCADE)

    
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
    remarks = models.TextField(null=True, blank=True)  # in hours

    def save(self, *args, **kwargs):
        # Calculate duration
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        self.duration = (end - start).seconds / 3600  # Convert to hours
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trainer.name} - {self.batch.name} - {self.date}"