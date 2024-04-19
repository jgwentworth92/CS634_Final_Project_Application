FROM python:3.8-slim

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy your Flask application and any scripts
COPY . .

# Run the table creation script before starting the Flask server
RUN chmod +x wait-for-it.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]