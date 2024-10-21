[Unit]
Description=FastAPI app
After=network.target

[Service]
WorkingDirectory=/home/ec2-user/gateway
ExecStart=/bin/bash -c 'source /home/ec2-user/gateway/venv/bin/activate && exec uvicorn gateway:app --host 0.0.0.0 --port 8080'
Restart=always

[Install]
WantedBy=multi-user.target