from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.db.models import Sum
from .models import BudgetDetails, MandatoryExpense, BasicNeedsExpense, SuddenExpense, BudgetSummary, UserAccount
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password


def register(request):
    error_message = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # Debugging print statements
        print(f"DEBUG: username='{username}', email='{email}', phone='{phone_number}'")

        # Ensure all fields are filled
        if not username or not phone_number or not email or not password:
            error_message= "All fields are required!"
            return render(request, "register.html", {"error_message": error_message})


        # Check if passwords match
        if password != confirm_password:
            error_message = "Passwords do not match!"
            return render(request, "register.html", {"error_message": error_message})


        # Check if email already exists
        if UserAccount.objects.filter(username=username).exists():
            error_message= "Username already registered!"
            return render(request, "register.html", {"error_message": error_message})

        
        if UserAccount.objects.filter(email=email).exists():
            error_message= "Email already registered!"
            return render(request, "register.html", {"error_message": error_message})

            

        # Check if phone number already exists
        if UserAccount.objects.filter(phone_number=phone_number).exists():
            error_message= "Phone number already registered!"
            return render(request, "register.html", {"error_message": error_message})


        # Save user
        user = UserAccount(
            username=username,
            phone_number=phone_number,
            email=email,
            password=make_password(password)  # Hash the password before saving
        )
        user.save()
        return redirect("login")

    return render(request, "register.html", {"error_message": error_message})

from django.contrib.auth.models import User

def login_view(request):
    error_message = ""

    if request.method == "POST":
        username = request.POST.get("username", "").strip() 
        password = request.POST.get("password", "").strip()  # Default to an empty string
        if not username or not password:
            error_message = "Username and password are required!"
        else:
            super_user = User.objects.filter(username=username).first()
            user = UserAccount.objects.filter(username=username).first()
            if super_user and super_user.is_superuser:
                return redirect("/admin/")

            if user and check_password(password, user.password):
                request.session["user_id"] = user.user_id
                request.session["username"] = user.username
                messages.success(request, "You have successfully logged in!")
                return redirect("home")
            else:
                error_message = "Invalid username or password!"

    return render(request, "login.html", {"error_message": error_message})


def logout_view(request):
    request.session.flush()
    messages.error(request, "You have successfully logged out!")
    return redirect("login")




def calculate_savings(user):
    """
    Calculate total savings for the logged-in user from all BudgetSummary entries.
    """
    total_savings = BudgetSummary.objects.filter(user=user).aggregate(total=Sum('savings'))['total']
    return total_savings if total_savings else 0

def first(request):
    # Ensure user is logged in
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")  # Redirect to login if not authenticated

    # Get the logged-in user
    user = UserAccount.objects.get(user_id=user_id)

    total_savings = calculate_savings(user)
    month = now().month
    year = now().year

    if request.method == "POST":
        actual_salary = float(request.POST["salary"])
        mandatory_limit = float(request.POST["mandatory_limit"])
        basic_needs_limit = float(request.POST["basic_needs_limit"])
        sudden_expenses_limit = float(request.POST["sudden_expenses_limit"])

        active_salary = mandatory_limit + basic_needs_limit + sudden_expenses_limit

        # Save budget details for the user
        budget = BudgetDetails(
            user=user,
            month=month,
            year=year,
            actual_salary=actual_salary,
            active_salary=active_salary,
            mandatory_limit=mandatory_limit,
            basic_needs_limit=basic_needs_limit,
            sudden_expenses_limit=sudden_expenses_limit,
        )
        budget.save()

        # Save initial budget summary for the user
        savings = actual_salary - active_salary

        summary = BudgetSummary(
            user=user,
            month=month,
            year=year,
            mandatory=0,
            basic_needs=0,
            sudden_expenses=0,
            savings=savings,
        )
        summary.save()

        return redirect("home")

    # Fetch last recorded budget details for the user
    latest_budget = BudgetDetails.objects.filter(user=user, month=month, year=year).last()
    

    # Fetch user-specific expenses
    mandatory_expense = MandatoryExpense.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0
    basic_needs_expense = BasicNeedsExpense.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0
    sudden_expense = SuddenExpense.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0

    

    # Calculate remaining salary (active salary) for the user
    if latest_budget:
        total_expenses = mandatory_expense + basic_needs_expense + sudden_expense
        remaining_salary = latest_budget.active_salary - total_expenses
    else:
        remaining_salary = 0

    return render(request, "first.html", {
        "user": user,
        "total_savings": total_savings,
        "remaining_salary": remaining_salary,
        "latest_budget": latest_budget,
    })



def check_and_allocate_funds(user, category, amount, month, year):
    budget = BudgetDetails.objects.filter(user=user, month=month, year=year).last()
    summary = BudgetSummary.objects.filter(user=user, month=month, year=year).last()

    if not budget or not summary:
        return False  # No budget exists yet

    # Calculate remaining funds in each category
    mandatory_remaining = budget.mandatory_limit - summary.mandatory
    basic_needs_remaining = budget.basic_needs_limit - summary.basic_needs
    sudden_expenses_remaining = budget.sudden_expenses_limit - summary.sudden_expenses

    required = amount

    if category == "Mandatory":
        if required <= mandatory_remaining:
            summary.mandatory += required
            required = 0
        else:
            summary.mandatory += mandatory_remaining
            required -= mandatory_remaining

            if required <= basic_needs_remaining:
                summary.basic_needs += required
                required = 0
            else:
                summary.basic_needs += basic_needs_remaining
                required -= basic_needs_remaining

                if required <= sudden_expenses_remaining:
                    summary.sudden_expenses += required
                    required = 0
                else:
                    summary.sudden_expenses += sudden_expenses_remaining
                    required -= sudden_expenses_remaining

    elif category == "Basic Needs":
        if required <= basic_needs_remaining:
            summary.basic_needs += required
            required = 0
        else:
            summary.basic_needs += basic_needs_remaining
            required -= basic_needs_remaining

            if required <= sudden_expenses_remaining:
                summary.sudden_expenses += required
                required = 0
            else:
                summary.sudden_expenses += sudden_expenses_remaining
                required -= sudden_expenses_remaining

    elif category == "Sudden Expense":
        if required <= sudden_expenses_remaining:
            summary.sudden_expenses += required
            required = 0
        else:
            summary.sudden_expenses += sudden_expenses_remaining
            required -= sudden_expenses_remaining

            if required <= basic_needs_remaining:
                summary.basic_needs += required
                required = 0
            else:
                summary.basic_needs += basic_needs_remaining
                required -= basic_needs_remaining

    # If there’s still required money left, take from total savings
    total_savings = get_total_savings(user)  # Get user's total savings
    if required > 0:
        if required <= total_savings:
            summary.savings -= required
        else:
            return False  # Not enough total savings available

    summary.save()
    return True  # Transaction successful


def get_total_savings(user):
    return (
        BudgetSummary.objects.filter(user=user).aggregate(total_savings=Sum("savings"))[
            "total_savings"
        ]
        or 0
    )


def get_remaining_salary(user, month, year):
    budget = BudgetDetails.objects.filter(user=user, month=month, year=year).last()
    summary = BudgetSummary.objects.filter(user=user, month=month, year=year).last()

    if not budget or not summary:
        return 0  # No budget data available

    spent_amount = summary.mandatory + summary.basic_needs + summary.sudden_expenses
    remaining_salary = budget.active_salary - spent_amount
    return remaining_salary


def home(request):
    # Ensure user is logged in
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")  # Redirect to login if not authenticated

    # Get the logged-in user
    user = UserAccount.objects.get(user_id=user_id)  


    if request.method == "POST":
        category = request.POST.get("category")
        expense = request.POST.get("expense")
        amount = float(request.POST.get("amount"))
        image = request.FILES.get("image")

        month = now().month
        year = now().year

        if check_and_allocate_funds(user, category, amount, month, year):
            if category == "Mandatory":
                expense_obj = MandatoryExpense(user=user, expense=expense, amount=amount, image=image)
                expense_obj.save()
            elif category == "Basic Needs":
                expense_obj = BasicNeedsExpense(user=user, expense=expense, amount=amount, image=image)
                expense_obj.save()
            elif category == "Sudden Expense":
                expense_obj = SuddenExpense(user=user, expense=expense, amount=amount, image=image)
                expense_obj.save()
            
            
            return redirect("home")
        else:
            return render(request, "home.html", {"error_message": "Insufficient funds!"})

    total_savings = get_total_savings(user)
    remaining_salary = get_remaining_salary(user, now().month, now().year)

    budget_details = BudgetDetails.objects.filter(user=user, month=now().month, year=now().year).first()
    budget_summary = BudgetSummary.objects.filter(user=user, month=now().month, year=now().year).first()

    return render(request, "home.html", {
        "user": user,
        "total_savings": total_savings,
        "remaining_salary": remaining_salary,
        "budget_details": budget_details,
        "budget_summary": budget_summary,
    })







import calendar
from django.shortcuts import render, redirect,get_object_or_404
from datetime import datetime, timedelta
from django.utils.timezone import get_current_timezone
from .models import UserAccount, MandatoryExpense, BasicNeedsExpense, SuddenExpense

def month_history(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = UserAccount.objects.get(user_id=user_id)

    now = datetime.now()
    current_month = now.month
    current_year = now.year

    month = int(request.GET.get("month", current_month))
    year = int(request.GET.get("year", current_year))

    expenses = []
    error_message = ""
    tz = get_current_timezone()

    try:
        all_expenses = []

        for exp in MandatoryExpense.objects.filter(user=user, timestamp__month=month, timestamp__year=year):
            ist_time = exp.timestamp.astimezone(tz) + timedelta(hours=5, minutes=30)
            all_expenses.append({
                "id": exp.id,
                "category": "Mandatory",
                "expense": exp.expense,
                "amount": exp.amount,
                "date": ist_time.strftime("%d-%m-%Y"),
                "time": ist_time.strftime("%H:%M"),
                "image_url": exp.image.url if exp.image else None
            })

        for exp in BasicNeedsExpense.objects.filter(user=user, timestamp__month=month, timestamp__year=year):
            ist_time = exp.timestamp.astimezone(tz) + timedelta(hours=5, minutes=30)
            all_expenses.append({
                "id": exp.id,
                "category": "Basic Needs",
                "expense": exp.expense,
                "amount": exp.amount,
                "date": ist_time.strftime("%d-%m-%Y"),
                "time": ist_time.strftime("%H:%M"),
                "image_url": exp.image.url if exp.image else None
            })

        for exp in SuddenExpense.objects.filter(user=user, timestamp__month=month, timestamp__year=year):
            ist_time = exp.timestamp.astimezone(tz) + timedelta(hours=5, minutes=30)
            all_expenses.append({
                "id": exp.id,
                "category": "Sudden Expense",
                "expense": exp.expense,
                "amount": exp.amount,
                "date": ist_time.strftime("%d-%m-%Y"),
                "time": ist_time.strftime("%H:%M"),
                "image_url": exp.image.url if exp.image else None
            })

        expenses = all_expenses

    except ValueError:
        error_message = "Invalid month or year selected."

    # Get month name from number
    month_name = calendar.month_name[month]

    # Send data to template
    return render(request, "month_history.html", {
        "user": user,
        "expenses": expenses,
        "selected_month": month,
        "selected_month_name": month_name,  # Pass month name
        "selected_year": year,
        "months_list": list(enumerate(calendar.month_name))[1:],  # (1, 'January') -> (2, 'February')
        "error_message": error_message,
    })


def delete_expense(request, expense_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = get_object_or_404(UserAccount, user_id=user_id)
    expense = None
    category = None

    # Identify the expense and category
    for model, cat_name in [
        (MandatoryExpense, "Mandatory"),
        (BasicNeedsExpense, "Basic Needs"),
        (SuddenExpense, "Sudden Expense"),
    ]:
        try:
            expense = model.objects.get(id=expense_id, user=user)
            category = cat_name
            break
        except model.DoesNotExist:
            continue

    if expense is None:
        return redirect("home")

    if request.method == "POST":
        summary = BudgetSummary.objects.filter(user=user, month=now().month, year=now().year).last()

        if summary:
            if category == "Mandatory":
                summary.mandatory -= expense.amount
            elif category == "Basic Needs":
                summary.basic_needs -= expense.amount
            elif category == "Sudden Expense":
                summary.sudden_expenses -= expense.amount
            summary.save()

        expense.delete()
        return redirect("month_history")  # Redirect to home after deletion

    return render(request, "delete.html", {"expense": expense, "category": category})

