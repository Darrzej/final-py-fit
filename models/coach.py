import numpy as np
import pandas as pd

class Coach:
    def __init__(self, user, stats_df, nutrition_df=None):
        self.user = user
        self.stats = stats_df
        self.nutrition = nutrition_df

    def analyze(self):
        feedback = []

        if self.stats.empty:
            return ["👋 Welcome! Please log your exercise PRs and nutrition to receive a physiological analysis."]

        # 1. Biological Analysis (Age, Height, Weight) - Using NumPy
        bmi = self.user.weight / ((self.user.height / 100) ** 2)
        
        if bmi < 18.5:
            feedback.append(f"📋 Body Metrics: BMI is {round(bmi, 1)} (Underweight). Focus on caloric density and progressive overload.")
        elif bmi > 25:
            feedback.append(f"📋 Body Metrics: BMI is {round(bmi, 1)} (High). Prioritize compound lifts to maximize metabolic cost.")

        if self.user.age > 40:
            feedback.append("🦴 Age Factor: At 40+, prioritize joint health and ensure 48-72 hours of recovery between heavy sessions.")
        elif self.user.age < 22:
            feedback.append("⚡ Development: Peak hormonal window detected. Optimal time for high-volume hypertrophy.")

        # 2. Nutrition Analysis (New Metrics)
        if self.nutrition is not None and not self.nutrition.empty:
            avg_protein = self.nutrition['protein'].mean()
            avg_calories = self.nutrition['calories'].mean()
            protein_target = self.user.weight * 2.0  # Scientific floor: 2g/kg
            
            if avg_protein < protein_target:
                feedback.append(f"🥩 Nutrition: Average protein ({round(avg_protein)}g) is below the required {round(protein_target)}g for your weight.")
            else:
                feedback.append(f"✅ Nutrition: Protein intake is optimal for muscle protein synthesis.")

            if self.user.goal == "bulk" and avg_calories < 2800:
                feedback.append("🍚 Bulking: Your calorie average suggests you are not in a sufficient surplus to maximize gains.")
            elif self.user.goal == "cut" and avg_calories > 2200:
                feedback.append("🥗 Cutting: Watch your caloric floor; ensure a 300-500 calorie deficit for sustainable fat loss.")

        # 3. Performance & Relative Strength
        for exercise in self.stats["name"].unique():
            ex_df = self.stats[self.stats["name"] == exercise].sort_values(by="updated_at")
            latest = ex_df.iloc[-1]
            rel_strength = latest['pr'] / self.user.weight

            if rel_strength < 0.75:
                feedback.append(f"🔬 {exercise}: Relative strength is {round(rel_strength, 2)}x bodyweight. Focus on linear progression.")
            elif rel_strength > 1.5:
                feedback.append(f"🏅 {exercise}: Advanced strength level ({round(rel_strength, 2)}x bodyweight). Use periodization.")

            if len(ex_df) > 1 and latest['pr'] <= ex_df.iloc[-2]['pr']:
                feedback.append(f"⚠️ Warning: {exercise} has stalled. Check if recovery or nutrition is the limiting factor.")

        return feedback