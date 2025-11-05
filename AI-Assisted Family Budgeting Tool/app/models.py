from django.db import models

class UserAccount(models.Model):
    user_id = models.AutoField(primary_key=True)  # Explicit primary key
    username = models.CharField(max_length=150,unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Store hashed passwords in production

    def __str__(self):
        return self.username


class BudgetDetails(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, to_field="user_id")  # Use user_id as FK
    month = models.IntegerField()
    year = models.IntegerField()
    actual_salary = models.FloatField() 
    active_salary = models.FloatField()
    mandatory_limit = models.FloatField()
    basic_needs_limit = models.FloatField()             
    sudden_expenses_limit = models.FloatField()

    def __str__(self):
        return f"Budget for {self.month}/{self.year} - {self.user.username}"


class MandatoryExpense(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, to_field="user_id")  # Use user_id as FK
    timestamp = models.DateTimeField(auto_now_add=True)
    expense = models.CharField(max_length=255)
    amount = models.FloatField()
    image = models.ImageField(upload_to='expenses/', null=True, blank=True) 

    def __str__(self):  
        return f"{self.expense} - {self.amount} ({self.user.username})"


class BasicNeedsExpense(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, to_field="user_id")  # Use user_id as FK
    timestamp = models.DateTimeField(auto_now_add=True)
    expense = models.CharField(max_length=255)
    amount = models.FloatField()
    image = models.ImageField(upload_to='expenses/', null=True, blank=True) 

    def __str__(self):
        return f"{self.expense} - {self.amount} ({self.user.username})"


class SuddenExpense(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, to_field="user_id")  # Use user_id as FK
    timestamp = models.DateTimeField(auto_now_add=True)
    expense = models.CharField(max_length=255)
    amount = models.FloatField()
    image = models.ImageField(upload_to='expenses/', null=True, blank=True) 

    def __str__(self):
        return f"{self.expense} - {self.amount} ({self.user.username})"


class BudgetSummary(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, to_field="user_id")  # Use user_id as FK
    month = models.IntegerField()
    year = models.IntegerField()
    mandatory = models.FloatField()
    basic_needs = models.FloatField()
    sudden_expenses = models.FloatField()
    savings = models.FloatField()   

    def __str__(self):
        return f"Summary for {self.month}/{self.year} - {self.user.username}"
