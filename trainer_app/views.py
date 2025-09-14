from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Trainer, Batch, DailyClassLog, Profile
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from functools import wraps
import csv

# ✅ Helper function role check
def get_user_role(user):
    if hasattr(user, "profile"):
        return user.profile.role
    return "read_only"

# ✅ Role decorator
def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            role = get_user_role(request.user)
            if role not in allowed_roles:
                return redirect("index")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ------------------- HOME PAGE -------------------
@login_required
def index(request):
    role = get_user_role(request.user)

    # agar trainer profile hi nahi hai aur role admin bhi nahi hai toh add trainer bhejo
    if not hasattr(request.user, 'trainer') and role != "admin":
        return redirect('add_trainer')

    if role == "admin":
        trainers = Trainer.objects.all()
        batches = Batch.objects.all()
    else:
        trainers = Trainer.objects.filter(user=request.user)
        batches = Batch.objects.filter(trainer__user=request.user)

    logs = DailyClassLog.objects.filter(date=timezone.now().date(), trainer__user=request.user)

    trainer_progress = []
    for trainer in trainers:
        daily_hours = sum(log.duration for log in logs if log.trainer == trainer)
        progress_percentage = (daily_hours / trainer.expected_daily_hours) * 100 if trainer.expected_daily_hours else 0
        remaining_hours = trainer.expected_daily_hours - daily_hours
        trainer_progress.append({
            'trainer': trainer,
            'daily_hours': daily_hours,
            'remaining_hours': max(0, remaining_hours),
            'progress_percentage': min(progress_percentage, 100)
        })
    
    return render(request, 'index.html', {
        'trainer_progress': trainer_progress,
        'batches': batches,
        'role': role,
        'user': request.user
    })


# ------------------- TRAINERS -------------------
@login_required
@role_required(["admin", "read_write", "read_only"])  # read_only bhi allow karo
def add_trainer(request):
    # agar already trainer bana hai → sidha index bhej do
    if Trainer.objects.filter(user=request.user).exists():
        return redirect("index")

    # agar role read_only hai to uska trainer banana allow karo (sirf ek baar)
    if request.method == "POST":
        name = request.POST.get("name")
        subjects = request.POST.get("subjects")
        expected_daily_hours = request.POST.get("expected_daily_hours")

        Trainer.objects.create(
            user=request.user,
            name=name,
            subjects=subjects,
            expected_daily_hours=expected_daily_hours
        )

        # ✅ uske baad role ko read_write kar do taki loop na ho
        profile = request.user.profile
        profile.role = "read_write"
        profile.save()

        return redirect("index")

    return render(request, "add_trainer.html")



@login_required
@role_required(["admin"])
def add_trainer_admin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        name = request.POST.get("name")
        subjects = request.POST.get("subjects")
        expected_daily_hours = request.POST.get("expected_daily_hours")

        if User.objects.filter(username=username).exists():
            return render(request, "add_trainer_admin.html", {
                "error": "Username already taken!"
            })

        user = User.objects.create_user(username=username, email=email, password=password)

        # ✅ Profile create ya update
        profile, created = Profile.objects.get_or_create(user=user)
        if created:
            profile.role = "read_write"
            profile.save()

        Trainer.objects.create(
            user=user,
            name=name,
            subjects=subjects,
            expected_daily_hours=expected_daily_hours
        )

        return redirect("index")

    return render(request, "add_trainer_admin.html")



@login_required
@role_required(["admin", "read_write"])
def edit_trainer(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)

    # sirf admin ya khud edit kar sake
    if get_user_role(request.user) != "admin" and trainer.user != request.user:
        return redirect("index")

    if request.method == 'POST':
        trainer.name = request.POST['name']
        trainer.subjects = request.POST['subjects']
        trainer.expected_daily_hours = float(request.POST['expected_daily_hours'])
        trainer.save()
        return redirect('index')
    return render(request, 'edit_trainer.html', {'trainer': trainer})


@login_required
@role_required(["admin"])
def delete_trainer(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)
    trainer.delete()
    return redirect('index')


# ------------------- BATCHES -------------------
@login_required
@role_required(["admin", "read_write"])
def add_batch(request):
    if request.method == 'POST':
        name = request.POST['name']
        course = request.POST['course']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        trainer_id = request.POST['trainer']
        Batch.objects.create(
            name=name,
            course=course,
            start_date=start_date,
            end_date=end_date,
            trainer_id=trainer_id
        )
        return redirect('index')

    trainers = Trainer.objects.all()
    return render(request, 'add_batch.html', {'trainers': trainers})


# ------------------- CLASS LOGS -------------------
@login_required
@role_required(["admin", "read_write"])
def add_log(request):
    if request.method == 'POST':
        trainer_id = request.POST['trainer']
        batch_id = request.POST['batch']
        date = datetime.strptime(request.POST['date'], "%d-%m-%Y").date()
        start_time = datetime.strptime(request.POST['start_time'], "%I:%M:%p").time()
        end_time = datetime.strptime(request.POST['end_time'], "%I:%M:%p").time()
        remarks = request.POST.get('remarks', '')
        DailyClassLog.objects.create(
            trainer_id=trainer_id,
            batch_id=batch_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            remarks=remarks
        )
        return redirect('index')

    trainers = Trainer.objects.all()
    batches = Batch.objects.all()
    return render(request, 'add_log.html', {'trainers': trainers, 'batches': batches})


# ------------------- REPORTS -------------------
def batch_details(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    logs = DailyClassLog.objects.filter(batch=batch)
    return render(request, 'batch_details.html', {'batch': batch, 'logs': logs})


def weekly_report(request):
    start_date = timezone.now().date() - timedelta(days=7)
    logs = DailyClassLog.objects.filter(date__gte=start_date)
    
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="weekly_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Trainer', 'Batch', 'Date', 'Duration (hrs)'])
        for log in logs:
            writer.writerow([log.trainer.name, log.batch.name, log.date, log.duration])
        return response
    
    return render(request, 'weekly_report.html', {'logs': logs, 'start_date': start_date})


# ------------------- USER MANAGEMENT (ADMIN ONLY) -------------------
@login_required
@role_required(["admin"])
def manage_users(request):
    users = User.objects.all()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        new_role = request.POST.get("role")

        user = User.objects.get(id=user_id)
        profile, created = Profile.objects.get_or_create(user=user)
        profile.role = new_role
        profile.save()

        return redirect("manage_users")

    return render(request, "manage_users.html", {"users": users})

# ------------------- AFTER LOGIN -------------------
@login_required
def after_login(request):
    role = get_user_role(request.user)

    # agar user trainer hai toh index bhejo
    if role in ["read_write", "read_only"]:
        try:
            request.user.trainer
            return redirect("index")
        except Trainer.DoesNotExist:
            return redirect("add_trainer")

    # agar admin hai toh seedha index bhejo
    if role == "admin":
        return redirect("index")

    # fallback
    return redirect("index")

