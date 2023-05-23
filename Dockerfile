FROM python:3.9

WORKDIR /app

# Clone the GitHub repository
RUN git clone https://github.com/obidose/SAH-QIP .

# Install dependencies
COPY requirements.txt .
COPY input/input.xlsx input/
COPY assets/style.css
RUN pip install --no-cache-dir -r requirements.txt

# Expose the desired port
EXPOSE 8050

# Start the application
CMD ["python", "main.py"]