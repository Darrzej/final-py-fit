class Coach:
    def __init__(self, user, stats_df):
        self.user = user
        self.stats = stats_df

    def analyze(self):
        feedback = []

        if self.stats.empty:
            return ["Start adding your PRs to get coaching feedback."]

        for exercise in self.stats["name"].unique():
            ex_df = self.stats[self.stats["name"] == exercise]
            latest = ex_df.iloc[0]

            feedback.append(
                f"💪 {exercise}: PR {latest['pr']}kg for {latest['reps']} reps."
            )

        if self.user.frequency < 3:
            feedback.append("⚠️ Try training at least 3 times per week for better progress.")

        if self.user.goal == "bulk":
            feedback.append("🍗 Focus on progressive overload and calorie surplus.")
        elif self.user.goal == "cut":
            feedback.append("🔥 Maintain strength while in calorie deficit.")

        return feedback
