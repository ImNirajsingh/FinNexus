import sys
from pathlib import Path

# import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# from src.analytics.category_analysis import (
#     analyze_categories,
#     get_top_expense_category,
#     get_top_income_category,
# )

# # ============================================================
# # MONTHLY ANALYSIS
# # ============================================================
# monthly = analyze_monthly_trends(df)

# print("\n" + "=" * 80)
# print("                    MONTHLY ANALYSIS")
# print("=" * 80)
# print(monthly.to_string(index=False))

# # ============================================================
# # HIGHEST EXPENSE MONTH
# # ============================================================
# highest_expense = get_highest_expense_month(df)

# print("\n" + "=" * 80)
# print("                 HIGHEST EXPENSE MONTH")
# print("=" * 80)
# print(highest_expense.to_string())

# # ============================================================
# # HIGHEST INCOME MONTH
# # ============================================================
# highest_income = get_highest_income_month(df)

# print("\n" + "=" * 80)
# print("                  HIGHEST INCOME MONTH")
# print("=" * 80)
# print(highest_income.to_string())


# df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "balance_reconciliation.csv")


# # ============================================================
# # CATEGORY ANALYSIS
# # ============================================================

# categories = analyze_categories(df)

# print("\n" + "=" * 100)
# print("                         CATEGORY ANALYSIS")
# print("=" * 100)

# print(
#     categories.to_string(index=False)
# )


# # ============================================================
# # TOP EXPENSE CATEGORIES
# # ============================================================

# top_expenses = get_top_expense_category(
#     df,
#     n=10,
# )

# print("\n" + "=" * 100)
# print("                    TOP EXPENSE CATEGORIES")
# print("=" * 100)

# print(
#     top_expenses[
#         [
#             "category",
#             "transaction_count",
#             "total_expense",
#             "expense_percentage",
#         ]
#     ].to_string(index=False)
# )


# # ============================================================
# # TOP INCOME CATEGORIES
# # ============================================================

# top_income = get_top_income_category(
#     df,
#     n=10,
# )

# print("\n" + "=" * 100)
# print("                     TOP INCOME CATEGORIES")
# print("=" * 100)

# print(
#     top_income[
#         [
#             "category",
#             "transaction_count",
#             "total_income",
#         ]
#     ].to_string(index=False)
# )



#  for recurring

import pandas as pd

from src.analytics.recurring import (
    detect_recurring_transaction,
)


df = pd.read_csv(
    PROJECT_ROOT / "data" / "processed" / "cleaned_transactions.csv"
)


# ============================================================
# RECURRING TRANSACTION ANALYSIS
# ============================================================

recurring = detect_recurring_transaction(
    df,
    min_occurrences=3,
    amount_tolerance=0.10,
    interval_tolerance_days=7,
)


print("\n" + "=" * 120)
print("                    RECURRING TRANSACTION ANALYSIS")
print("=" * 120)

if recurring.empty:

    print("No recurring transactions detected.")

else:

    print(
        recurring.to_string(index=False)
    )