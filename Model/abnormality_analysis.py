import collections
import os
import joblib
import numpy as np
from pykalman import KalmanFilter
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
warnings.filterwarnings("ignore")
from tensorflow import keras
import pandas as pd
import json
import tempfile
import zipfile

import warnings

class MineHazardDetector:

    def __init__(self, model_path, scaler_path, threshold_path, window_size=15):
        self.window_size = window_size
        self.sensor_names = ["CO2", "Dust", "Temperature", "Humidity"]
        self.buffer = collections.deque(maxlen=window_size)

        # Load artifacts
        self.scaler = joblib.load(scaler_path)
        self.model = self.load_patched_keras_model(model_path)
        self.threshold = joblib.load(threshold_path)

        # Initialize Kalman Filter
        self.kf = KalmanFilter(
            transition_matrices=[1],
            observation_matrices=[1],
            initial_state_covariance=1.0,
            observation_covariance=0.1,
            transition_covariance=0.01,
        )
    def load_patched_keras_model(self,model_path):
        """Removes unsupported serialization keys (like quantization_config) on the fly."""
        with tempfile.NamedTemporaryFile(suffix=".keras", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        with (
            zipfile.ZipFile(model_path, "r") as zin,
            zipfile.ZipFile(tmp_path, "w") as zout,
        ):
            for item in zin.infolist():
                buffer = zin.read(item.filename)
                if item.filename == "config.json":
                    config_str = buffer.decode("utf-8")
                    # Strip out the invalid quantization_config parameter
                    config = json.loads(config_str)

                    def remove_quant(obj):
                        if isinstance(obj, dict):
                            obj.pop("quantization_config", None)
                            for v in obj.values():
                                remove_quant(v)
                        elif isinstance(obj, list):
                            for item in obj:
                                remove_quant(item)

                    remove_quant(config)
                    buffer = json.dumps(config).encode("utf-8")
                zout.writestr(item, buffer)

        return keras.models.load_model(tmp_path)
    def _smooth_window(self, raw_window):
        """Applies Kalman smoothing across the active time window for each sensor."""
        smoothed = np.zeros_like(raw_window)
        for col_idx in range(raw_window.shape[1]):
            col_data = raw_window[:, col_idx]
            state_means, _ = self.kf.smooth(col_data)
            smoothed[:, col_idx] = state_means.flatten()
        return smoothed

    def process_reading(self, raw_sensor_reading):
        """Pass a single sensor reading: [CO2, Dust, Temp, Humidity]"""
        self.buffer.append(raw_sensor_reading)

        
        if len(self.buffer) < self.window_size:
            print(
                f"System warming up... ({len(self.buffer)}/{self.window_size} readings)"
            )
            return None

        # 2. Kalman Filtering across the window
        raw_window = np.array(self.buffer)
        smoothed_window = self._smooth_window(raw_window)
        smoothed_df = pd.DataFrame(smoothed_window, columns=self.sensor_names)
        # 3. Standard Scaling
        scaled_window = self.scaler.transform(smoothed_df)

        # 4. Reshape to 3D for Keras (1, window_size, 4)
        input_3d = np.expand_dims(scaled_window, axis=0)

        # 5. Prediction / Reconstruction
        reconstruction = self.model.predict(input_3d, verbose=0)

        # 6. Error & Anomaly Detection
        current_reality = input_3d[0, -1, :]
        current_prediction = reconstruction[0, -1, :]
        sensor_errors = np.square(current_reality - current_prediction)
        residual = float(np.mean(sensor_errors))

        anomalies = []
        for i in range(len(self.sensor_names)):
            if sensor_errors[i] > self.threshold[i]:
                condition = (
                    "High"
                    if current_reality[i] > current_prediction[i]
                    else "Abnormal Drop in"
                )
                anomalies.append(f"{condition} {self.sensor_names[i]}")

        # 7. Hazard Reporting
        if anomalies:
            culprits = " & ".join(anomalies)
            print(f"🚨 HAZARD DETECTED! MSE: {residual:.4f} | Cause: {culprits}")
            return {
                "status": "HAZARD",
                "mse": residual,
                "anomalies": anomalies,
                "raw_reading": raw_sensor_reading,
            }

        print(f"✅ Safe. MSE: {residual:.4f}")
        return {"status": "SAFE", "mse": residual}


if __name__ == "__main__":
    detector = MineHazardDetector(
    model_path="C:\\mineppl\\model.keras",
    scaler_path="C:\\mineppl\\scaler.joblib",
    threshold_path="C:\\mineppl\\threshold.joblib",
    window_size=15,
    )
    data = [
        [940.3492, 685.6914, 17.9873, 28.0390],
        [940.5546, 762.1284, 18.0161, 28.3379],
        [943.0637, 827.0192, 17.9835, 28.2966],
        [946.5980, 883.5387, 17.9652, 28.4065],
        [950.1189, 933.5810, 17.9838, 28.3957],
        [954.8472, 980.8977, 18.0175, 28.4297],
        [960.7607, 1015.1974, 18.0625, 28.6506],
        [965.9173, 1050.9227, 17.9565, 28.4224],
        [972.3065, 1076.4367, 17.9836, 28.2342],
        [978.5256, 1098.5895, 17.9579, 28.2577],
        [985.5031, 1115.7292, 18.0234, 28.0451],
        [993.3144, 1132.1161, 18.0561, 27.8180],
        [999.6073, 1141.0317, 17.9860, 27.5559],
        [1007.5008, 1148.3308, 17.9841, 27.6453],
        [1014.2613, 1150.4572, 18.0212, 27.2982],
        [1021.0132, 1153.2147, 17.9963, 27.2887],
        [1028.0802, 1149.6311, 18.0413, 27.1266],
        [1034.9747, 1149.1251, 17.9944, 27.0150],
        [1041.3780, 1144.4902, 18.0016, 26.9625],
        [1047.0044, 1139.9481, 18.0002, 26.9520],
        [1051.9851, 1134.4153, 18.0344, 27.1820],
        [1056.5811, 1133.1324, 18.0965, 26.9902],
        [1060.8670, 1129.6583, 18.0387, 27.2539],
        [1064.1096, 1122.5512, 18.0623, 27.7168],
        [1068.6658, 1118.5556, 18.0126, 27.6507],
        [2200.0000, 1120.6080, 18.0698, 28.0400],  # Injected: High CO2 spike
        [1077.3139, 1120.4663, 18.0480, 28.1022],
        [1082.5538, 1122.7513, 18.0676, 28.3326],
        [1089.1719, 1128.9546, 18.1092, 28.7561],
        [1096.9595, 1134.6475, 18.0713, 28.7832],
        [1105.1493, 1147.8384, 18.0441, 29.1865],
        [1116.1346, 1162.2909, 18.0945, 29.2714],
        [1127.1067, 1179.9917, 18.1027, 29.4350],
        [1138.7586, 1197.7237, 18.1481, 29.2454],
        [1148.8596, 1216.7987, 18.1208, 29.3021],
        [1159.8189, 2400.0000, 38.5000, 29.2891],  # Injected: High Dust & Temp
        [1167.9138, 2450.0000, 39.1000, 29.2453],
        [1173.8930, 2380.0000, 38.8000, 29.1623],
        [1175.7338, 1283.1496, 18.1502, 29.1798],
        [1175.2474, 1293.8839, 18.1841, 29.0765],
        [1169.4300, 1299.8161, 18.1356, 29.0055],
        [1159.1597, 1299.8189, 18.1775, 28.7771],
        [1144.6996, 1291.5895, 18.2576, 28.8102],
        [1127.4367, 1284.4645, 18.2237, 28.3894],
        [1106.8109, 1274.8135, 18.1972, 28.5012],
        [1085.7446, 1262.1898, 18.3005, 28.4260],
        [1066.8250, 1250.4104, 18.3234, 28.2318],
        [1046.6563, 1236.9497, 18.2597, 28.2724],
        [1030.0099, 1226.7261, 18.3409, 28.2556],
        [1016.4077, 1217.0931, 18.3811, 28.0526],
        [1007.4807, 1208.7392, 18.3947, 5.0000],  # Injected: Low Humidity drop
        [1003.7632, 1206.3417, 18.4055, 27.8850],
        [1005.7684, 1209.8906, 18.3993, 28.0107],
        [1010.5609, 1212.9352, 18.3715, 27.9874],
        [1019.0355, 1216.3377, 18.4144, 28.0385],
        [1028.3886, 1224.8080, 18.4430, 28.1590],
        [1039.4334, 1230.3367, 18.4929, 28.0930],
        [1050.8360, 1233.1825, 18.4725, 28.2537],
        [1061.2668, 1231.0046, 18.5095, 28.3110],
        [1068.7869, 1232.4211, 18.5459, 28.4119],
        [1075.4537, 1222.8356, 18.5809, 28.3231],
        [1077.5903, 1214.1376, 18.5678, 28.1374],
        [1077.7398, 1193.2927, 18.6093, 28.4205],
        [1073.1874, 1173.0901, 18.6129, 28.5340],
        [1067.2039, 1153.7554, 18.6774, 28.4828],
        [
            1800.0000,
            1130.9432,
            8.0000,
            10.0000,
        ],  # Injected: High CO2 + Temp/Humidity drops
        [1850.0000, 1111.2861, 7.5000, 9.5000],
        [1790.0000, 1095.7024, 8.2000, 10.5000],
        [1028.9629, 1083.4727, 18.7997, 28.6283],
        [1016.6387, 1077.6697, 18.7947, 28.4649],
        [1006.4986, 1077.5981, 18.7745, 28.7690],
        [997.0659, 1087.9094, 18.8128, 28.7305],
        [988.2141, 1107.7972, 18.7982, 28.8304],
        [979.4976, 1132.6260, 18.9192, 28.9268],
        [970.7010, 1159.6683, 18.9162, 28.9998],
        [964.1651, 1186.3265, 18.9639, 29.0440],
        [957.2530, 1218.6795, 18.9452, 29.0172],
        [950.9817, 1243.9606, 19.0121, 29.1684],
        [944.6541, 1271.0485, 19.0600, 29.0839],
        [938.6374, 1288.9794, 19.0749, 29.1444],
    ]

    columns = ["CO2", "Dust", "Temperature", "Humidity"]
    df = pd.DataFrame(data, columns=columns)
    for index, row in df.iterrows():
        detector.process_reading(row.values)