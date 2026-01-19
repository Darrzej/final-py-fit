import numpy as np

class Coach:
    def __init__(self, user, stats_df):
        self.user = user
        self.stats = stats_df

    def analyze(self):
        feedback = []

        if self.stats.empty:
            return ["👋 Welcome! Please log your exercise PRs to receive a personalized physiological analysis."]

        # 1. Biological Profile Analysis (Age, Height, Weight)
        # Using NumPy for BMI calculation
        bmi = self.user.weight / ((self.user.height / 100) ** 2)
        
        if bmi < 18.5:
            feedback.append(f"📋 Body Metrics: Your BMI is {round(bmi, 1)}. To support muscle protein synthesis, ensure a caloric surplus with at least 2g of protein per kg of body weight.")
        elif bmi > 25:
            feedback.append(f"📋 Body Metrics: With a BMI of {round(bmi, 1)}, prioritize compound lifts (Squats, Deadlifts) to maximize metabolic demand.")

        # 2. Age-Specific Recovery Advice
        if self.user.age > 40:
            feedback.append("🦴 Recovery: At age 40+, central nervous system recovery takes longer. Ensure 48 hours of rest between hitting the same muscle group.")
        elif self.user.age < 22:
            feedback.append("⚡ Development: Your natural growth hormone levels are peak. This is an optimal window for high-volume hypertrophy training.")

        # 3. Performance & Relative Strength Analysis
        for exercise in self.stats["name"].unique():
            # Get history for this exercise sorted by date
            ex_df = self.stats[self.stats["name"] == exercise].sort_values(by="updated_at")
            latest = ex_df.iloc[-1]
            
            # Calculate Relative Strength (Weight Lifted / Body Weight)
            rel_strength = latest['pr'] / self.user.weight

            if rel_strength < 0.75:
                feedback.append(f"🔬 {exercise}: Your relative strength is {round(rel_strength, 2)}x bodyweight. Focus on linear progression—add 2.5kg every session.")
            elif rel_strength > 1.5:
                feedback.append(f"🏅 {exercise}: Advanced strength detected ({round(rel_strength, 2)}x bodyweight). Transition to periodized blocks (Heavy/Light weeks) to avoid overtraining.")

            # Plateau Detection
            if len(ex_df) > 1:
                previous = ex_df.iloc[-2]
                if latest['pr'] <= previous['pr']:
                    feedback.append(f"⚠️ Warning: Your {exercise} has stalled. Decrease weight by 10% for one week (Deload) to reset your strength curve.")

        # 4. Goal-Frequency Alignment
        if self.user.goal == "bulk" and self.user.frequency < 4:
            feedback.append("🍗 Goal Optimization: For effective bulking, a training frequency of 3 days may be insufficient. Aim for 4-5 days to increase weekly volume.")

        return feedback