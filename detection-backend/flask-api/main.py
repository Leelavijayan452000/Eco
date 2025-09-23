#!/usr/bin/env python3

import os
import sys
import sqlite3
import threading
from datetime import datetime

import cv2
import numpy as np
from ultralytics import YOLO

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QProgressBar,
    QMessageBox,
    QFrame,
    QSizePolicy,
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "best (1).pt")
DB_PATH = os.path.join(os.path.dirname(__file__), "predictions.db")
PRED_INTERVAL_MS = 3000  # predict every 3000ms
VIDEO_FPS_MS = 30        # update video every ~30ms

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            label TEXT,
            confidence REAL,
            timestamp TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bins (
            name TEXT PRIMARY KEY,
            level INTEGER
        )
        """
    )
    bins_init = [("Recycle", 10), ("Non-Recycle", 10), ("Organic", 10)]
    for name, level in bins_init:
        cursor.execute(
            "INSERT OR IGNORE INTO bins (name, level) VALUES (?, ?)", (name, level)
        )
    conn.commit()
    conn.close()


init_db()

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"YOLO model not found at {MODEL_PATH}. Place 'best (1).pt' there."
    )

try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Error loading YOLO model: {e}")

model_lock = threading.Lock()

def save_prediction(filename: str, label: str, confidence: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO predictions (filename, label, confidence, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (filename, label, confidence, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

LABEL_MAP = {
    "Recyclable": "Recycle",
    "Recyclable_item": "Recycle",
    "Non-Recyclable": "Non-Recycle",
    "NonRecyclable": "Non-Recycle",
    "Organic": "Organic",
    "Compost": "Organic",
    "Recycle": "Recycle",
    "Non-Recycle": "Non-Recycle",
}


class BottleWidget(QWidget):
    """A vertical progress visualization styled like a bottle / fill."""

    def __init__(self, title: str, color: str = "#0ea5e9"):
        super().__init__()
        self.title = title
        self.color = color
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(6, 6, 6, 6)

        lbl = QLabel(self.title)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-weight: 700; color: #e5e7eb;")
        lbl.setFixedHeight(22)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(10)
        self.bar.setTextVisible(True)
        self.bar.setFormat("%p%")
        self.bar.setAlignment(Qt.AlignCenter)
        self.bar.setOrientation(Qt.Vertical)
        self.bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.apply_style(active=False)

        layout.addWidget(lbl)
        layout.addWidget(self.bar, stretch=1)
        self.setLayout(layout)

    def set_value(self, v: int):
        v = max(0, min(100, int(v)))
        self.bar.setValue(v)

    def get_value(self) -> int:
        return self.bar.value()

    def apply_style(self, active: bool = False):
        # Use gradient-like fill and border glow when active
        border = f"box-shadow: 0 0 14px {self.color};" if active else ""
        stylesheet = f"""
        QProgressBar {{
            border: 5px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0,0,0,0.25), stop:1 rgba(0,0,0,0.45));
            color: #f9fafb;
            padding: 2px;
        }}
        QProgressBar::chunk {{
            border-radius: 10px;
            margin: 2px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {self.color}, stop:1 rgba(0,0,0,0.25));
        }}
        """
        self.bar.setStyleSheet(stylesheet)


class SortyxApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sortyx | Eco-Saver 🌱")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("background-color: #0b1220; color: #f9fafb;")
        self.cap = None
        self.stream_opened = False
        self.active_prediction = {"label": None, "confidence": None}
        self.init_ui()
        self._open_camera()
        self.start_timers()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Sortyx | Eco-Saver 🌱")
        title.setFont(QFont("Inter", 20, QFont.Bold))
        title.setStyleSheet("color: #f9fafb;")
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        btn_reset = QPushButton("Reset Levels")
        btn_notify = QPushButton("Notify")

        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_notify.setCursor(Qt.PointingHandCursor)

        btn_reset.clicked.connect(self.handle_reset)
        btn_notify.clicked.connect(self.handle_notify)

        btn_reset.setStyleSheet(self.button_style("#ef4444"))
        btn_notify.setStyleSheet(self.button_style("#10b981"))

        header.addWidget(title)
        header.addWidget(btn_reset)
        header.addWidget(btn_notify)

        main_layout.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(18)

        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet(
            "background-color: #000; border-radius: 12px; border: 1px solid rgba(255,255,255,0.04);"
        )
        self.video_frame.setFixedSize(640, 360)
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel()  # will show the camera feed
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setStyleSheet("background: transparent;")

        self.overlay_label = QLabel("", parent=self.video_label)
        self.overlay_label.setStyleSheet(
            "color: #e5e7eb; font-size: 16px; background: rgba(0,0,0,0.45); padding: 8px; border-radius: 8px;"
        )
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.setFixedSize(self.video_frame.size())
        self.overlay_label.hide()

        video_layout.addWidget(self.video_label)
        self.video_frame.setLayout(video_layout)

        left_col.addWidget(self.video_frame)

        bins_row = QHBoxLayout()
        bins_row.setSpacing(12)

        self.bottle_recycle = BottleWidget("Recycle", color="#0ea5e9")
        self.bottle_non_recycle = BottleWidget("Non-Recycle", color="#f97316")
        self.bottle_organic = BottleWidget("Organic", color="#84cc16")

        bins_row.addWidget(self.bottle_recycle, stretch=1)
        bins_row.addWidget(self.bottle_non_recycle, stretch=1)
        bins_row.addWidget(self.bottle_organic, stretch=1)

        left_col.addLayout(bins_row)

        content.addLayout(left_col, stretch=3)

        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        self.dashboard_cards = {}
        for name, color in [
            ("Recycle", "#0ea5e9"),
            ("Non-Recycle", "#f97316"),
            ("Organic", "#84cc16"),
        ]:
            card = QFrame()
            card.setStyleSheet(
                "background: #0f1724; border-radius: 12px; padding: 12px; border: 2px solid rgba(255,255,255,0.1);"
            )
            card_layout = QHBoxLayout()
            card_layout.setSpacing(12)

            small_bottle = QProgressBar()
            small_bottle.setOrientation(Qt.Vertical)
            small_bottle.setRange(0, 100)
            small_bottle.setValue(10)
            small_bottle.setFixedSize(56, 170)
            small_bottle.setStyleSheet(
                f"""
                QProgressBar{{ border-radius: 12px; background: #111827; }}
                QProgressBar::chunk{{ background: {color}; border-radius: 10px; }}
                """
            )

            txt_area = QVBoxLayout()
            title_lbl = QLabel(name)
            title_lbl.setStyleSheet("font-weight: 700; color: #f9fafb;")
            desc_lbl = QLabel(
                "Bottles, cans, paper..." if name == "Recycle" else
                "Broken toys, dirty items" if name == "Non-Recycle" else
                "Food scraps, fruit peels"
            )
            desc_lbl.setStyleSheet("color: #9ca3af;")
            desc_lbl.setWordWrap(True)

            full_msg = QLabel("")
            full_msg.setStyleSheet("color: #facc15; font-weight: 700;")
            full_msg.hide()

            txt_area.addWidget(title_lbl)
            txt_area.addWidget(desc_lbl)
            txt_area.addWidget(full_msg)

            card_layout.addWidget(small_bottle)
            card_layout.addLayout(txt_area)
            card.setLayout(card_layout)

            right_col.addWidget(card)
            self.dashboard_cards[name] = {
                "card": card,
                "small_bottle": small_bottle,
                "desc": desc_lbl,
                "full_msg": full_msg,
            }

        content.addLayout(right_col, stretch=2)

        main_layout.addLayout(content)
        self.setLayout(main_layout)

    def button_style(self, bg: str) -> str:
        return f"""
        QPushButton {{
            background-color: {bg};
            color: #f9fafb;
            border-radius: 10px;
            padding: 8px 14px;
            font-weight: 700;
        }}
        QPushButton:hover {{
            transform: translateY(-2px);
            opacity: 0.95;
        }}
        """

    def _open_camera(self):

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == "nt" else 0)
        if not self.cap.isOpened():

            self.stream_opened = False
            self.overlay_label.setText("Camera access denied or unavailable.")
            self.overlay_label.show()
        else:
            self.stream_opened = True
            self.overlay_label.hide()

    def start_timers(self):
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video_frame)
        self.video_timer.start(VIDEO_FPS_MS)


        self.pred_timer = QTimer()
        self.pred_timer.timeout.connect(self.run_prediction_once)
        self.pred_timer.start(PRED_INTERVAL_MS)

    def update_video_frame(self):
        if not self.cap or not self.stream_opened:

            if not self.stream_opened:
                self._open_camera()
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qt_img).scaled(
            self.video_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pix)

        self.overlay_label.resize(self.video_label.size())

        if not self.overlay_label.isHidden():
            self.overlay_label.hide()

    def run_prediction_once(self):
       
        if not self.cap or not self.stream_opened:
            self.overlay_label.setText("Starting camera...")
            self.overlay_label.show()
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)

        try:
            with model_lock:
                results = model.predict(frame, verbose=False)
        except Exception as e:
            print("Model inference error:", e)
            return

        if not results or not hasattr(results[0], "probs"):
            return

        probs = results[0].probs
        class_id = int(probs.top1)
        label = results[0].names[class_id]
        confidence = float(probs.top1conf)

        # Save to DB
        try:
            save_prediction("frame.jpg", label, confidence)
        except Exception as e:
            print("DB save error:", e)
        mapped = LABEL_MAP.get(label, None)
        if mapped is None:
            if label in ("Recycle", "Non-Recycle", "Organic"):
                mapped = label
        if mapped and confidence > 0.7:
            self.handle_bin_update(mapped, confidence)

    def handle_bin_update(self, bin_name: str, confidence: float):
        widget_map = {
            "Recycle": self.bottle_recycle,
            "Non-Recycle": self.bottle_non_recycle,
            "Organic": self.bottle_organic,
        }
        dashboard_map = self.dashboard_cards

        if bin_name not in widget_map:
            return

        w = widget_map[bin_name]
        new_val = min(100, w.get_value() + 1)#10........
        w.set_value(new_val)

        dashboard_map[bin_name]["small_bottle"].setValue(new_val)
        if new_val >= 100:
            dashboard_map[bin_name]["full_msg"].setText("Bin Full! Please empty.")
            dashboard_map[bin_name]["full_msg"].show()
        else:
            dashboard_map[bin_name]["full_msg"].hide()

        w.apply_style(active=True)
        QTimer.singleShot(1400, lambda: w.apply_style(active=False))

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT level FROM bins WHERE name=?", (bin_name,))
            row = cursor.fetchone()
            current = row[0] if row else 10
            new_db_level = min(100, current + 10)
            cursor.execute("UPDATE bins SET level=? WHERE name=?", (new_db_level, bin_name))
            conn.commit()
            conn.close()
        except Exception as e:
            print("DB bin update error:", e)

    def handle_reset(self):
        for widget in (self.bottle_recycle, self.bottle_non_recycle, self.bottle_organic):
            widget.set_value(10)
            widget.apply_style(active=False)

        for name in self.dashboard_cards:
            self.dashboard_cards[name]["small_bottle"].setValue(10)
            self.dashboard_cards[name]["full_msg"].hide()

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            defaults = [("Recycle", 10), ("Non-Recycle", 10), ("Organic", 10)]
            for n, lv in defaults:
                cursor.execute("UPDATE bins SET level=? WHERE name=?", (lv, n))
            conn.commit()
            conn.close()
        except Exception as e:
            print("DB reset error:", e)

    def handle_notify(self):
        QMessageBox.information(self, "Notify", "Notification dispatched (placeholder).")

    def closeEvent(self, event):
      
        try:
            if self.cap and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = SortyxApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
