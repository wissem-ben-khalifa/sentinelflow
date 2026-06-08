"""
SentinelFlow - Isolation Forest Model
Unsupervised anomaly detection for tabular data.
Detects abnormal records without requiring labeled data.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path
from config.logging_config import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path("models/isolation_forest")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class IsolationForestDetector:
    """
    Isolation Forest based anomaly detector.
    Trains on clean data and detects anomalies in new data.
    """

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        """
        contamination: expected proportion of anomalies in the dataset.
        0.05 means we expect about 5% of records to be anomalies.
        """
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False

    def prepare_features(self, df: pd.DataFrame, feature_columns: list) -> np.ndarray:
        """
        Extract and scale numeric features from dataframe.
        Fills missing values with column median before scaling.
        """
        features = df[feature_columns].copy()
        for col in feature_columns:
            features[col] = pd.to_numeric(features[col], errors="coerce")
            features[col] = features[col].fillna(features[col].median())
        return features.values

    def train(self, df: pd.DataFrame, feature_columns: list) -> None:
        """
        Train the Isolation Forest on clean data.
        Should only be called with known-good records.
        """
        logger.info(f"Training Isolation Forest on {len(df)} records")
        logger.info(f"Features: {feature_columns}")

        self.feature_columns = feature_columns
        X = self.prepare_features(df, feature_columns)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True

        logger.info("Isolation Forest training complete")

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict anomalies in new data.
        Returns the dataframe with added columns:
            anomaly_score: float, higher means more anomalous
            is_anomaly: boolean
            anomaly_label: normal or anomaly
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before calling predict")

        X = self.prepare_features(df, self.feature_columns)
        X_scaled = self.scaler.transform(X)

        # Isolation Forest returns -1 for anomalies, 1 for normal
        raw_predictions = self.model.predict(X_scaled)

        # Score: higher = more anomalous (inverted from sklearn convention)
        raw_scores = self.model.decision_function(X_scaled)
        anomaly_scores = 1 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-10)

        result = df.copy()
        result["is_anomaly"] = raw_predictions == -1
        result["anomaly_score"] = np.round(anomaly_scores, 4)
        result["anomaly_label"] = result["is_anomaly"].map({True: "anomaly", False: "normal"})

        anomaly_count = int(result["is_anomaly"].sum())
        logger.info(f"Detected {anomaly_count} anomalies out of {len(df)} records")

        return result

    def save(self, model_name: str) -> None:
        """Save model and scaler to disk."""
        model_path = MODEL_DIR / f"{model_name}_model.pkl"
        scaler_path = MODEL_DIR / f"{model_name}_scaler.pkl"
        meta_path = MODEL_DIR / f"{model_name}_meta.pkl"

        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)
        with open(scaler_path, "wb") as f:
            pickle.dump(self.scaler, f)
        with open(meta_path, "wb") as f:
            pickle.dump(self.feature_columns, f)

        logger.info(f"Model saved to {model_path}")

    def load(self, model_name: str) -> None:
        """Load model and scaler from disk."""
        model_path = MODEL_DIR / f"{model_name}_model.pkl"
        scaler_path = MODEL_DIR / f"{model_name}_scaler.pkl"
        meta_path = MODEL_DIR / f"{model_name}_meta.pkl"

        with open(model_path, "rb") as f:
            self.model = pickle.load(f)
        with open(scaler_path, "rb") as f:
            self.scaler = pickle.load(f)
        with open(meta_path, "rb") as f:
            self.feature_columns = pickle.load(f)

        self.is_trained = True
        logger.info(f"Model loaded from {model_path}")