import pandas as pd
import numpy as np

def compute_progress(df):
    """Return basic stats like average weight and volume."""
    if df.empty:
        return None
    df["volume"] = df["sets"] * df["reps"] * df["weight"]
    avg_volume = df.groupby("exercise")["volume"].mean().round(2)
    return avg_volume

def recommend_next_workout(df):
    """Suggest increasing or maintaining weights based on trends."""
    if df.empty:
        return "Start logging your first workout!"
    last = df.groupby("exercise")["weight"].tail(1)
    recommendation = []
    for ex, w in last.items():
        trend = df[df["exercise"] == ex]["weight"].diff().mean()
        if trend > 0:
            recommendation.append(f"✅ Keep increasing {ex} gradually (avg +{trend:.1f} kg)")
        elif trend < 0:
            recommendation.append(f"⚠️ You’ve decreased on {ex}, try to recover your previous weight")
        else:
            recommendation.append(f"➡️ Maintain your {ex} performance for now")
    return "\n".join(recommendation)
