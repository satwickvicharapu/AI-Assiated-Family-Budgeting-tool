from django.contrib import admin
from .models import BudgetDetails, MandatoryExpense, BasicNeedsExpense, SuddenExpense, BudgetSummary,UserAccount

# Registering models
admin.site.register(BudgetDetails)
admin.site.register(MandatoryExpense)
admin.site.register(BasicNeedsExpense)
admin.site.register(SuddenExpense)
admin.site.register(BudgetSummary)
admin.site.register(UserAccount)
