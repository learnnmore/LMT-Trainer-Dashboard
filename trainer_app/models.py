from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ------------------- ROLE SYSTEM -------------------
class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('read_write', 'Read & Write'),
        ('read_only', 'Read Only'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# ------------------- TRAINER -------------------
class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    name = models.CharField(max_length=100)
    subjects = models.CharField(max_length=200)
    expected_daily_hours = models.FloatField()

    def __str__(self):
        return self.name


# ------------------- BATCH -------------------
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
    course = models.CharField(max_length=50, choices=IT_COURSES)
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


# ------------------- CLASS LOG -------------------
class DailyClassLog(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.FloatField()
    remarks = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Calculate duration automatically
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        self.duration = (end - start).seconds / 3600
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trainer.name} - {self.batch.name} - {self.date}"

# ------------------- AUTO CREATE PROFILE -------------------
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)   # default role = read_only
    else:
        instance.profile.save()