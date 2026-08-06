class FinancialPlanner:
    def calculate_plan(self, salary: float, expenses: float, goal: str, risk: str) -> dict:
        """Calculate financial plan based on user inputs"""
        money_available = salary - expenses
        savings_percent = (money_available / salary * 100) if salary > 0 else 0
        emergency_fund_target = expenses * 6  # 6 months of expenses
        suggested_investment = money_available * 0.8  # Invest 80% of savings

        # Adjust based on risk
        if risk == "low":
            suggested_investment = money_available * 0.6
        elif risk == "high":
            suggested_investment = money_available * 0.9

        return {
            "money_available": money_available,
            "savings_percent": savings_percent,
            "emergency_fund_target": emergency_fund_target,
            "suggested_investment": suggested_investment,
            "goal": goal,
            "risk": risk
        }


planner = FinancialPlanner()