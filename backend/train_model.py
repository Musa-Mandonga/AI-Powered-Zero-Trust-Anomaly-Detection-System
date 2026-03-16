"""
Train and save the Isolation Forest model and scaler for anomaly detection.
This script replicates the training process from model_training.ipynb.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
import joblib
import warnings

warnings.filterwarnings('ignore')

# Paths
DATA_PATH = Path(__file__).parent / "data" / "auth_logs_raw.csv"
MODEL_PATH = Path(__file__).parent / "isoforest_model.pkl"
SCALER_PATH = Path(__file__).parent / "scaler.pkl"

def main():
    print("Starting model training...")
    
    # Load data
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
    
    print(f"Loading data from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"   Loaded {len(df)} records")
    
    # Apply Zero-Trust labeling
    print("Applying Zero-Trust labeling...")
    ZERO_TRUST_NORMAL_LABEL = "normal"
    df["binary_label"] = (df["event_label"] != ZERO_TRUST_NORMAL_LABEL).astype(int)
    df["is_anomaly"] = df["binary_label"]
    print(f"   Normal events: {(df['is_anomaly'] == 0).sum()}")
    print(f"   Anomaly events: {(df['is_anomaly'] == 1).sum()}")
    
    # Extract hour from access_time
    print("Extracting hour from access_time...")
    df["hour"] = pd.to_datetime(df["access_time"], format='%H:%M:%S', errors='coerce').dt.hour.fillna(0).astype(int)
    
    # Encode categorical columns
    print("Encoding categorical features...")
    categorical_cols = ['user_id', 'device_id', 'ip_address', 'location', 'resource_accessed']
    for col in categorical_cols:
        encoder = LabelEncoder()
        df[col] = encoder.fit_transform(df[col].astype(str))
    
    # Prepare feature matrix
    print("Preparing feature matrix...")
    features = ['user_id', 'device_id', 'ip_address', 'location', 
                'login_success', 'hour', 'resource_accessed', 'bytes_transferred']
    X = df[features]
    y = df['is_anomaly']
    
    # Scale features
    print("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split data
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Train on normal data only (Zero-Trust approach)
    X_train_normal = X_train[y_train == 0]
    expected_contamination = min(max(y_train.mean(), 1e-3), 0.49)
    print(f"   Training on {len(X_train_normal)} normal samples")
    print(f"   Expected contamination: {expected_contamination:.4f}")
    
    # Train Isolation Forest
    print("Training Isolation Forest model...")
    iso_final = IsolationForest(contamination=expected_contamination, random_state=42)
    iso_final.fit(X_train_normal)
    print("   Model trained successfully")
    
    # Evaluate on test set
    y_pred = iso_final.predict(X_test)
    y_pred_binary = np.where(y_pred == -1, 1, 0)
    accuracy = (y_pred_binary == y_test).mean()
    print(f"   Test accuracy: {accuracy:.4f}")
    
    # Save model and scaler
    print("Saving model and scaler...")
    joblib.dump(iso_final, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"   Model saved to {MODEL_PATH}")
    print(f"   Scaler saved to {SCALER_PATH}")
    
    print("\nTraining complete! You can now run the API server.")

if __name__ == "__main__":
    main()

