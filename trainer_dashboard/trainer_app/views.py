from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import Trainer, Batch, DailyClassLog
from django.utils import timezone
from datetime import datetime, date as datetime_date
from datetime import timedelta
import csv

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def index(request):
    try:
        trainer = request.user.trainer
    except Trainer.DoesNotExist:
        if request.user.is_authenticated:
            trainer = Trainer.objects.create(
                user=request.user,
                name=request.user.username,
                subjects='General Subjects',
                expected_daily_hours=8.0
            )
        else:
            return redirect('login')
    
    batches = Batch.objects.filter(trainer=trainer)
    logs = DailyClassLog.objects.filter(trainer=trainer, date=timezone.now().date())
    
    daily_hours = sum(log.duration for log in logs)
    progress_percentage = (daily_hours / trainer.expected_daily_hours) * 100 if trainer.expected_daily_hours else 0
    remaining_hours = trainer.expected_daily_hours - daily_hours
    trainer_progress = [{
        'trainer': trainer,
        'daily_hours': daily_hours,
        'remaining_hours': max(0, remaining_hours),
        'progress_percentage': min(progress_percentage, 100)
    }]
    
    return render(request, 'index.html', {'trainer_progress': trainer_progress, 'batches': batches})

@login_required
def add_trainer(request):
    if not request.user.is_superuser:
        return redirect('index')
    if request.method == 'POST':
        name = request.POST['name']
        subjects = request.POST['subjects']
        expected_daily_hours = request.POST['expected_daily_hours']
        username = request.POST['username']
        password = request.POST.get('password', '')
        use_existing_user = request.POST.get('use_existing_user', False)

        try:
            expected_daily_hours = float(expected_daily_hours)
            if expected_daily_hours <= 0:
                raise ValueError("Expected daily hours must be positive.")
            
            if use_existing_user:
                if not User.objects.filter(username=username).exists():
                    return render(request, 'add_trainer.html', {
                        'error': 'Username does not exist.',
                        'form_data': {
                            'name': name,
                            'subjects': subjects,
                            'expected_daily_hours': expected_daily_hours,
                            'username': username,
                            'use_existing_user': 'on'
                        }
                    })
                user = User.objects.get(username=username)
                if Trainer.objects.filter(user=user).exists():
                    return render(request, 'add_trainer.html', {
                        'error': 'This user is already a trainer.',
                        'form_data': {
                            'name': name,
                            'subjects': subjects,
                            'expected_daily_hours': expected_daily_hours,
                            'username': username,
                            'use_existing_user': 'on'
                        }
                    })
            else:
                if User.objects.filter(username=username).exists():
                    return render(request, 'add_trainer.html', {
                        'error': 'Username already exists. Choose a different username or use an existing user.',
                        'form_data': {
                            'name': name,
                            'subjects': subjects,
                            'expected_daily_hours': expected_daily_hours,
                            'username': username
                        }
                    })
                if not password:
                    return render(request, 'add_trainer.html', {
                        'error': 'Password is required for new users.',
                        'form_data': {
                            'name': name,
                            'subjects': subjects,
                            'expected_daily_hours': expected_daily_hours,
                            'username': username
                        }
                    })
                user = User.objects.create_user(username=username, password=password)

            Trainer.objects.create(
                name=name,
                subjects=subjects,
                expected_daily_hours=expected_daily_hours,
                user=user
            )
            return redirect('index')
        except ValueError as e:
            return render(request, 'add_trainer.html', {
                'error': str(e),
                'form_data': {
                    'name': name,
                    'subjects': subjects,
                    'expected_daily_hours': expected_daily_hours,
                    'username': username,
                    'use_existing_user': 'on' if use_existing_user else ''
                }
            })
    return render(request, 'add_trainer.html')

@login_required
def edit_trainer(request, trainer_id):
    if not request.user.is_superuser:
        return redirect('index')
    trainer = get_object_or_404(Trainer, id=trainer_id)
    if request.method == 'POST':
        try:
            trainer.name = request.POST['name']
            trainer.subjects = request.POST['subjects']
            trainer.expected_daily_hours = float(request.POST['expected_daily_hours'])
            if trainer.expected_daily_hours <= 0:
                raise ValueError("Expected daily hours must be positive.")
            trainer.save()
            return redirect('index')
        except ValueError as e:
            return render(request, 'edit_trainer.html', {
                'trainer': trainer,
                'error': str(e)
            })
    return render(request, 'edit_trainer.html', {'trainer': trainer})

@login_required
def delete_trainer(request, trainer_id):
    if not request.user.is_superuser:
        return redirect('index')
    trainer = get_object_or_404(Trainer, id=trainer_id)
    trainer.user.delete()
    trainer.delete()
    return redirect('index')

@login_required
def add_batch(request):
    if not request.user.is_superuser:
        return redirect('index')
    if request.method == 'POST':
        try:
            name = request.POST['name']
            course = request.POST['course']
            start_date = request.POST['start_date']
            trainer_id = request.POST['trainer']
            Batch.objects.create(name=name, course=course, start_date=start_date, trainer_id=trainer_id)
            return redirect('index')
        except ValueError as e:
            return render(request, 'add_batch.html', {
                'trainers': Trainer.objects.all(),
                'error': str(e)
            })
    trainers = Trainer.objects.all()
    return render(request, 'add_batch.html', {'trainers': trainers})

@login_required
def add_log(request):
    try:
        trainer = request.user.trainer
    except Trainer.DoesNotExist:
        trainer = Trainer.objects.create(
            user=request.user,
            name=request.user.username,
            subjects='General Subjects',
            expected_daily_hours=8.0
        )
    if request.method == 'POST':
        try:
            batch_id = request.POST['batch']
            date_str = request.POST['date']
            start_time_str = request.POST['start_time']
            end_time_str = request.POST['end_time']
            
            # Convert date string to datetime.date
            year, month, day = map(int, date_str.split('-'))
            date = datetime_date(year, month, day)
            
            # Convert time strings to datetime.time
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Create log
            DailyClassLog.objects.create(
                trainer=trainer,
                batch_id=batch_id,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            return redirect('index')
        except (ValueError, TypeError) as e:
            return render(request, 'add_log.html', {
                'trainer': trainer,
                'batches': Batch.objects.filter(trainer=trainer),
                'error': str(e) or 'Invalid date or time format.'
            })
    batches = Batch.objects.filter(trainer=trainer)
    return render(request, 'add_log.html', {'trainer': trainer, 'batches': batches})

@login_required
def batch_details(request, batch_id):
    try:
        trainer = request.user.trainer
    except Trainer.DoesNotExist:
        trainer = Trainer.objects.create(
            user=request.user,
            name=request.user.username,
            subjects='General Subjects',
            expected_daily_hours=8.0
        )
    batch = get_object_or_404(Batch, id=batch_id, trainer=trainer)
    logs = DailyClassLog.objects.filter(batch=batch, trainer=trainer)
    return render(request, 'batch_details.html', {'batch': batch, 'logs': logs})

@login_required
def weekly_report(request):
    try:
        trainer = request.user.trainer
    except Trainer.DoesNotExist:
        trainer = Trainer.objects.create(
            user=request.user,
            name=request.user.username,
            subjects='General Subjects',
            expected_daily_hours=8.0
        )
    start_date = timezone.now().date() - timedelta(days=7)
    logs = DailyClassLog.objects.filter(trainer=trainer, date__gte=start_date)
    
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="weekly_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Trainer', 'Batch', 'Date', 'Duration (hrs)'])
        for log in logs:
            writer.writerow([log.trainer.name, log.batch.name, log.date, log.duration])
        return response
    
    return render(request, 'weekly_report.html', {'logs': logs, 'start_date': start_date})