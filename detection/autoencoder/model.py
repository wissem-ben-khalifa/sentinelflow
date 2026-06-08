"""
SentinelFlow - Autoencoder Model
Deep learning based anomaly detection.
Learns normal data patterns and flags records
with high reconstruction error as anomalies.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import pickle
from config.logging_config import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path("models/autoencoder")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class AutoencoderDetector:
    """
    Autoencoder based anomaly detector.
    Architecture:
        Input -> Dense 128 -> Dense 64 -> Latent 16 -> Dense 64 -> Dense 128 -> Output
    Trained only on normal records.
    Anomalies are detected by high reconstruction error.
    """

    def __init__(self, threshold_percentile: float = 95):
        """
        threshold_percentile: percentile of reconstruction errors on training data
        used to set the anomaly threshold.
        95 means the top 5% of errors are flagged as anomalies.
        """
        self.threshold_percentile = threshold_percentile
        self.model = None
        self.scaler = None
        self.threshold = None
        self.feature_columns = None
        self.is_trained = False

    def build_model(self, input_dim: int):
        """Build the autoencoder architecture using TensorFlow."""
        import tensorflow as tf
        from tensorflow.keras import layers, Model

        inputs = tf.keras.Input(shape=(input_dim,))

        # Encoder
        x = layers.Dense(128, activation="relu")(inputs)
        x = layers.Dense(64, activation="relu")(x)
        encoded = layers.Dense(16, activation="relu")(x)

        # Decoder
        x = layers.Dense(64, activation="relu")(encoded)
        x = layers.Dense(128, activation="relu")(x)
        decoded = layers.Dense(input_dim, activation="linear")(x)

        model = Model(inputs, decoded)
        model.compile(optimizer="adam", loss="mse")

        return model

    def prepare_features(self, df: pd.DataFrame, feature_columns: list) -> np.ndarray:
        """Extract and scale features from dataframe."""
        from sklearn.preprocessing import StandardScaler

        features = df[feature_columns].copy()
        for col in feature_columns:
            features[col] = pd.to_numeric(features[col], errors="coerce")
            features[col] = features[col].fillna(features[col].median())

        return features.values

    def train(self, df: pd.DataFrame, feature_columns: list, epochs: int = 50) -> None:
        """
        Train the autoencoder on clean data only.
        Sets the anomaly threshold based on training reconstruction errors.
        """
        from sklearn.preprocessing import StandardScaler

        logger.info(f"Training Autoencoder on {len(df)} records for {epochs} epochs")
        logger.info(f"Features: {feature_columns}")

        self.feature_columns = feature_columns

        X = self.prepare_features(df, feature_columns)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        input_dim = X_scaled.shape[1]
        self.model = self.build_model(input_dim)

        self.model.fit(
            X_scaled,
            X_scaled,
            epochs=epochs,
            batch_size=32,
            shuffle=True,
            validation_split=0.1,
            verbose=0
        )

        # Set threshold based on training reconstruction errors
        reconstructions = self.model.predict(X_scaled, verbose=0)
        errors = np.mean(np.power(X_scaled - reconstructions, 2), axis=1)
        self.threshold = float(np.percentile(errors, self.threshold_percentile))

        self.is_trained = True
        logger.info(f"Autoencoder training complete. Threshold: {self.threshold:.6f}")

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies using reconstruction error.
        Returns dataframe with added columns:
            reconstruction_error: float
            is_anomaly_ae: boolean
            anomaly_score_ae: normalized score 0 to 1
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before calling predict")

        X = self.prepare_features(df, self.feature_columns)
        X_scaled = self.scaler.transform(X)

        reconstructions = self.model.predict(X_scaled, verbose=0)
        errors = np.mean(np.power(X_scaled - reconstructions, 2), axis=1)

        # Normalize scores to 0-1 range
        min_err = errors.min()
        max_err = errors.max()
        normalized_scores = (errors - min_err) / (max_err - min_err + 1e-10)

        result = df.copy()
        result["reconstruction_error"] = np.round(errors, 6)
        result["is_anomaly_ae"] = errors > self.threshold
        result["anomaly_score_ae"] = np.round(normalized_scores, 4)

        anomaly_count = int(result["is_anomaly_ae"].sum())
        logger.info(f"Autoencoder detected {anomaly_count} anomalies out of {len(df)} records")

        return result

    def save(self, model_name: str) -> None:
        """Save model, scaler and threshold to disk."""
        model_path = MODEL_DIR / f"{model_name}_model.keras"
        scaler_path = MODEL_DIR / f"{model_name}_scaler.pkl"
        meta_path = MODEL_DIR / f"{model_name}_meta.pkl"

        self.model.save(model_path)

        with open(scaler_path, "wb") as f:
            pickle.dump(self.scaler, f)

        with open(meta_path, "wb") as f:
            pickle.dump({
                "threshold": self.threshold,
                "feature_columns": self.feature_columns,
                "threshold_percentile": self.threshold_percentile
            }, f)

        logger.info(f"Autoencoder saved to {model_path}")

    def load(self, model_name: str) -> None:
        """Load model, scaler and threshold from disk."""
        import tensorflow as tf

        model_path = MODEL_DIR / f"{model_name}_model.keras"
        scaler_path = MODEL_DIR / f"{model_name}_scaler.pkl"
        meta_path = MODEL_DIR / f"{model_name}_meta.pkl"

        self.model = tf.keras.models.load_model(model_path)

        with open(scaler_path, "rb") as f:
            self.scaler = pickle.load(f)

        with open(meta_path, "rb") as f:
            meta = pickle.load(f)
            self.threshold = meta["threshold"]
            self.feature_columns = meta["feature_columns"]
            self.threshold_percentile = meta["threshold_percentile"]

        self.is_trained = True
        logger.info(f"Autoencoder loaded from {model_path}")