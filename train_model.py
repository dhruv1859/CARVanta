import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Load dataset
df = pd.read_csv("data/antigen_database.csv")

# Features
X = df[
    [
        "mean_tumor_expression",
        "mean_normal_expression",
        "stability_score",
        "literature_support"
    ]
]

# Target
y = df["viability_label"]

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# Model (STRONGER)
model = RandomForestClassifier(n_estimators=100)

model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)

print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(model, "models/car_t_model.pkl")

print("\n✅ Model retrained & saved")