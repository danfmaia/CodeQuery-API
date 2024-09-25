# Commands

<!-- TODO: Rewrite history to purge sensitive data in this file. -->

## Core

lsof -i :5001 && ps aux | grep ngrok

### Testing

source .env && curl -H "X-API-KEY: $API_KEY" https://codequery.dev/files/structure

curl -H "X-API-KEY: $API_KEY" http://$EC2_HOST:8080/files/structure

## Gateway

cd /home/danfmaia/\_repos/CodeQuery-API/gateway && source .env

source .env

### Terraform

terraform init | terraform plan | terraform apply

### Gateway Management

source .env && ssh -i $KEY_PATH $EC2_USER@$EC2_HOST

**Upload files:**

scp -i $KEY_PATH .env gateway.py requirements.txt $EC2_USER@$EC2_HOST:/home/$EC2_USER/gateway

scp -i $KEY_PATH .env $EC2_USER@$EC2_HOST:/home/$EC2_USER/gateway

source .env && curl -H "X-API-KEY: $API_KEY" https://codequery.dev/files/structure

## Gateway

cd /home/danfmaia/\_repos/CodeQuery-API/gateway && source .env

source .env

### Terraform

terraform init

terraform plan

terraform apply

### Gateway Management

ssh -i $KEY_PATH $EC2_USER@$EC2_HOST

**Upload files:**

scp -i $KEY_PATH .env gateway.py requirements.txt $EC2_USER@$EC2_HOST:/home/$EC2_USER/gateway

scp -i $KEY_PATH gateway.py $EC2_USER@$EC2_HOST:/home/$EC2_USER/gateway

**Restart server:**

ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "sudo systemctl daemon-reload && sudo systemctl restart fastapi && sudo systemctl status fastapi"

[Remote] sudo systemctl daemon-reload && sudo systemctl restart fastapi && sudo systemctl status fastapi

**Check server status:**

ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "sudo systemctl status fastapi"

[Remote] sudo systemctl status fastapi

[Remote] sudo journalctl -u fastapi.service -n 50

**Inspect FastAPI service spec:**

[Remote] sudo nano /etc/systemd/system/fastapi.service

**Misc:**

---

(venv) [ec2-user@ip-172-31-42-110 gateway]$ sudo chown ec2-user:ec2-user /home/ec2-user/gateway/.env
sudo chmod 644 /home/ec2-user/gateway/.env
(venv) [ec2-user@ip-172-31-42-110 gateway]$ sudo chown -R ec2-user:ec2-user /home/ec2-user/gateway/
sudo chmod -R 755 /home/ec2-user/gateway/

ssh -i "${KEY_PATH}" "${EC2_USER}@${EC2_HOST}" "sudo chown -R ec2-user:ec2-user /home/ec2-user/gateway/ && sudo chmod -R 755 /home/ec2-user/gateway/"
