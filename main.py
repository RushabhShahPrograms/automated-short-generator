import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, 
    QLineEdit, QPushButton, QStackedWidget, QComboBox, 
    QTextEdit, QMessageBox, QHBoxLayout, QFileDialog, 
    QProgressBar, QGroupBox, QSlider
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QFont
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from config import save_api_key, load_api_key
import subprocess
import os
import time

class APIKeyScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create a container widget for centered content
        container = QWidget()
        container_layout = QVBoxLayout()
        
        # Add welcome label with larger font
        welcome_label = QLabel("Welcome to Enhanced Gemini Chat Interface!")
        font = welcome_label.font()
        font.setPointSize(16)
        font.setBold(True)
        welcome_label.setFont(font)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(welcome_label)
        
        # Add spacing
        container_layout.addSpacing(20)
        
        # Add API key label with medium font
        api_label = QLabel("API Key:")
        api_font = api_label.font()
        api_font.setPointSize(12)
        api_label.setFont(api_font)
        api_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(api_label)
        
        # Add API key input with fixed width
        self.api_key_input = QLineEdit()
        self.api_key_input.setFixedWidth(400)
        self.api_key_input.setMinimumHeight(40)
        self.api_key_input.setPlaceholderText("Enter your Google API key")
        self.api_key_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.api_key_input, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add spacing
        container_layout.addSpacing(20)
        
        # Add submit button with fixed width
        self.submit_button = QPushButton("Submit")
        self.submit_button.setFixedWidth(200)
        self.submit_button.setMinimumHeight(40)
        font = self.submit_button.font()
        font.setPointSize(12)
        self.submit_button.setFont(font)
        container_layout.addWidget(self.submit_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        container.setLayout(container_layout)
        
        # Add container to main layout with stretch to center vertically
        main_layout.addStretch()
        main_layout.addWidget(container)
        main_layout.addStretch()
        
        self.setLayout(main_layout)

class MainScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Main horizontal layout for two columns
        layout = QHBoxLayout()
        
        # Left column (Input section)
        left_column = QVBoxLayout()
        
        # Model selection dropdown with larger size
        model_label = QLabel("Select Model:")
        font = model_label.font()
        font.setPointSize(12)
        model_label.setFont(font)
        left_column.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setMinimumHeight(40)
        self.model_combo.setFont(font)
        self.model_combo.addItems([
            "gemini-pro",
            "gemini-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-pro-002",
            "gemini-1.5-flash-002",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash-8b"
        ])
        left_column.addWidget(self.model_combo)
        
        left_column.addSpacing(20)
        
        # Prompt input
        prompt_label = QLabel("Prompt:")
        prompt_label.setFont(font)
        left_column.addWidget(prompt_label)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Enter your prompt for short-form video content")
        self.prompt_input.setFont(font)
        left_column.addWidget(self.prompt_input)
        
        # Generate button
        self.generate_button = QPushButton("Generate Content")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setFont(font)
        left_column.addWidget(self.generate_button)
        
        # Add left column to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_column)
        layout.addWidget(left_widget)
        
        # Right column (Output section)
        right_column = QVBoxLayout()
        
        # Response output
        response_label = QLabel("Generated Content:")
        response_label.setFont(font)
        right_column.addWidget(response_label)
        
        self.response_output = QTextEdit()
        self.response_output.setReadOnly(True)
        self.response_output.setFont(font)
        right_column.addWidget(self.response_output)
        
        # Copy button
        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.setMinimumHeight(50)
        self.copy_button.setFont(font)
        right_column.addWidget(self.copy_button)
        
        # Add right column to main layout
        right_widget = QWidget()
        right_widget.setLayout(right_column)
        layout.addWidget(right_widget)
        
        # Set equal stretch for both columns
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)
        
        self.setLayout(layout)

class AudioGenerationWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, text, ref_audio):
        super().__init__()
        self.text = text
        self.ref_audio = ref_audio
        
    def run(self):
        try:
            command = [
                "f5-tts_infer-cli",
                "--model", "F5-TTS",
                "--ref_audio", self.ref_audio,
                "--ref_text", "",
                "--gen_text", self.text,
                "--output_dir", "tests",
                "--output_file", "infer_cli_basic.wav"  # Set specific output filename
            ]
            
            # Start the process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Monitor the process output
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    if "%" in output:
                        try:
                            progress = int(output.split("%")[0].split("\r")[-1].strip())
                            self.progress.emit(progress)
                        except:
                            pass
            
            output_path = os.path.join("tests", "infer_cli_basic.wav")
            if process.returncode == 0 and os.path.exists(output_path):
                self.finished.emit(output_path)
            else:
                self.error.emit("Audio generation failed")
                
        except Exception as e:
            self.error.emit(str(e))

class TTSScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Main horizontal layout for two columns
        main_layout = QHBoxLayout()
        
        # Left Column
        left_column = QVBoxLayout()
        
        # Title
        title_label = QLabel("Text-to-Speech Generation")
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_column.addWidget(title_label)
        
        left_column.addSpacing(20)
        
        # Reference Audio Section with better styling
        ref_audio_label = QLabel("Reference Audio:")
        ref_audio_label.setFont(QFont("", 12))
        left_column.addWidget(ref_audio_label)
        
        ref_audio_layout = QHBoxLayout()
        self.ref_audio_path = QLineEdit()
        self.ref_audio_path.setText("sample_audio.mp3")
        self.ref_audio_path.setReadOnly(True)
        ref_audio_layout.addWidget(self.ref_audio_path)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.setFixedWidth(100)
        self.browse_button.clicked.connect(self.browse_audio)
        ref_audio_layout.addWidget(self.browse_button)
        left_column.addLayout(ref_audio_layout)
        
        left_column.addSpacing(20)
        
        # Generated Text Section
        text_label = QLabel("Generated Text (editable):")
        text_label.setFont(QFont("", 12))
        left_column.addWidget(text_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(200)  # Limit height
        left_column.addWidget(self.text_edit)
        
        left_column.addSpacing(20)
        
        # Generate Audio Button
        self.generate_button = QPushButton("Generate Audio")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setFont(QFont("", 12))
        left_column.addWidget(self.generate_button)
        
        left_column.addStretch()
        
        # Create left column widget
        left_widget = QWidget()
        left_widget.setLayout(left_column)
        main_layout.addWidget(left_widget)
        
        # Right Column
        right_column = QVBoxLayout()
        
        # Progress Section
        progress_group = QGroupBox("Generation Progress")
        progress_group.setFont(QFont("", 12))
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        right_column.addWidget(progress_group)
        
        # Audio Player Section
        player_group = QGroupBox("Audio Player")
        player_group.setFont(QFont("", 12))
        player_layout = QVBoxLayout()
        
        # Add slider for audio progress
        self.audio_slider = QSlider(Qt.Orientation.Horizontal)
        self.audio_slider.setEnabled(False)
        player_layout.addWidget(self.audio_slider)
        
        # Time labels
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.duration_label = QLabel("0:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.duration_label)
        player_layout.addLayout(time_layout)
        
        # Player controls
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Play")
        self.play_button.setEnabled(False)
        self.play_button.setFixedWidth(100)
        self.play_button.clicked.connect(self.play_audio)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.setFixedWidth(100)
        self.stop_button.clicked.connect(self.stop_audio)
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        
        player_layout.addLayout(controls_layout)
        player_group.setLayout(player_layout)
        right_column.addWidget(player_group)
        
        # Download Button
        self.download_button = QPushButton("Download Audio")
        self.download_button.setMinimumHeight(50)
        self.download_button.setFont(QFont("", 12))
        self.download_button.hide()
        right_column.addWidget(self.download_button)
        
        right_column.addStretch()
        
        # Create right column widget
        right_widget = QWidget()
        right_widget.setLayout(right_column)
        main_layout.addWidget(right_widget)
        
        # Set equal stretch for both columns
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 1)
        
        self.setLayout(main_layout)
        
        # Initialize media player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Connect media player signals
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.audio_slider.sliderMoved.connect(self.set_position)
        
    def update_position(self, position):
        self.audio_slider.setValue(position)
        self.current_time_label.setText(self.format_time(position))
        
    def update_duration(self, duration):
        self.audio_slider.setRange(0, duration)
        self.duration_label.setText(self.format_time(duration))
        
    def set_position(self, position):
        self.player.setPosition(position)
        
    def format_time(self, ms):
        s = round(ms / 1000)
        m, s = divmod(s, 60)
        return f"{m}:{s:02d}"
        
    def play_audio(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_button.setText("Play")
        else:
            self.player.play()
            self.play_button.setText("Pause")
            
    def stop_audio(self):
        self.player.stop()
        self.play_button.setText("Play")

    def browse_audio(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Audio", "", "Audio Files (*.mp3 *.wav)"
        )
        if file_name:
            self.ref_audio_path.setText(file_name)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemini Content Generator")
        self.setMinimumSize(600, 400)
        
        # Create stacked widget to manage screens
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Initialize screens
        self.api_screen = APIKeyScreen()
        self.main_screen = MainScreen()
        self.tts_screen = TTSScreen()
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.api_screen)
        self.stacked_widget.addWidget(self.main_screen)
        self.stacked_widget.addWidget(self.tts_screen)
        
        # Setup connections
        self.setup_connections()
        
        # Check for existing API key
        api_key = load_api_key()
        if api_key:
            self.initialize_gemini(api_key)
            self.stacked_widget.setCurrentWidget(self.main_screen)
        else:
            self.stacked_widget.setCurrentWidget(self.api_screen)

    def setup_connections(self):
        self.api_screen.submit_button.clicked.connect(self.handle_api_key_submit)
        self.main_screen.generate_button.clicked.connect(self.generate_content)
        self.main_screen.copy_button.clicked.connect(self.copy_to_clipboard)
        self.main_screen.copy_button.setText("Convert to Speech")
        self.main_screen.copy_button.clicked.connect(self.show_tts_screen)
        self.tts_screen.generate_button.clicked.connect(self.generate_audio)
        self.tts_screen.download_button.clicked.connect(self.download_audio)

    def handle_api_key_submit(self):
        api_key = self.api_screen.api_key_input.text().strip()
        if api_key:
            try:
                self.initialize_gemini(api_key)
                save_api_key(api_key)
                self.stacked_widget.setCurrentWidget(self.main_screen)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid API key: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Please enter an API key")

    def initialize_gemini(self, api_key):
        genai.configure(api_key=api_key)
        self.setup_safety_settings()

    def setup_safety_settings(self):
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

    def generate_content(self):
        prompt = self.main_screen.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Warning", "Please enter a prompt")
            return
            
        try:
            model = genai.GenerativeModel(
                self.main_screen.model_combo.currentText(),
                safety_settings=self.safety_settings
            )
            response = model.generate_content(prompt)
            
            if response.prompt_feedback.block_reason:
                self.main_screen.response_output.setText("Sorry, the prompt was blocked due to safety concerns.")
            else:
                self.main_screen.response_output.setText(response.text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.main_screen.response_output.toPlainText())
        QMessageBox.information(self, "Success", "Content copied to clipboard!")

    def show_tts_screen(self):
        # Set the generated text in TTS screen
        self.tts_screen.text_edit.setText(self.main_screen.response_output.toPlainText())
        self.tts_screen.download_button.hide()
        self.stacked_widget.setCurrentWidget(self.tts_screen)
        
    def generate_audio(self):
        try:
            generated_text = self.tts_screen.text_edit.toPlainText()
            ref_audio = self.tts_screen.ref_audio_path.text()
            
            # Show progress bar
            self.tts_screen.progress_bar.show()
            self.tts_screen.progress_bar.setValue(0)
            self.tts_screen.generate_button.setEnabled(False)
            
            # Create and start worker
            self.worker = AudioGenerationWorker(generated_text, ref_audio)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.audio_generation_finished)
            self.worker.error.connect(self.audio_generation_error)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate audio: {str(e)}")
            
    def update_progress(self, value):
        self.tts_screen.progress_bar.setValue(value)
        
    def audio_generation_finished(self, output_file):
        try:
            self.tts_screen.progress_bar.hide()
            self.tts_screen.generate_button.setEnabled(True)
            self.tts_screen.download_button.show()
            
            # Setup audio player with the generated file
            self.tts_screen.player.setSource(QUrl.fromLocalFile(output_file))
            self.tts_screen.play_button.setEnabled(True)
            self.tts_screen.stop_button.setEnabled(True)
            self.tts_screen.audio_slider.setEnabled(True)
            
            QMessageBox.information(self, "Success", "Audio generated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process output file: {str(e)}")
            self.tts_screen.progress_bar.hide()
            self.tts_screen.generate_button.setEnabled(True)

    def audio_generation_error(self, error_message):
        self.tts_screen.progress_bar.hide()
        self.tts_screen.generate_button.setEnabled(True)
        QMessageBox.critical(self, "Error", error_message)
            
    def download_audio(self):
        try:
            # Use the original generated file path
            source_path = os.path.join("tests", "infer_cli_basic.wav")
            
            if not os.path.exists(source_path):
                raise FileNotFoundError("Generated audio file not found")
                
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save Audio File", "", "Audio Files (*.wav)"
            )
            
            if save_path:
                # Copy the generated file to the selected location
                with open(source_path, 'rb') as src, open(save_path, 'wb') as dst:
                    dst.write(src.read())
                QMessageBox.information(self, "Success", "Audio file saved successfully!")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save audio: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()