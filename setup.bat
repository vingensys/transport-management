@echo off
cd /d "C:\Users\SSEDRG\Documents\Development"

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing required packages...
pip install --upgrade pip
pip install numpy matplotlib scikit-learn

:: Choose one of the following:
pip install tensorflow         :: # If you want to use TensorFlow
:: pip install torch torchvision  :: # Or comment the above line and use PyTorch

echo (Optional) Install Jupyter:
pip install notebook

echo Environment setup complete.
pause
