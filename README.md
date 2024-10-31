## **Installation Procedure**

Follow these steps to set up and run the application.

### **Tested Environment**

- **OS**: Amazon Linux 2
- **Python**: 3.9

**put the value of S3_BUCKET_NAME, YouTube_links.txt to the desired value**
---

### Installation Steps

```bash
# Install necessary packages
$ sudo yum -y install python-pip
$ sudo pip install flask gunicorn boto3 pytz
$ sudo yum install nginx -y
$ sudo mkdir /etc/nginx/sites-enabled

# Configure Nginx
$ sudo vim /etc/nginx/sites-enabled/flask_project.conf
server {
    listen 80;
    server_name {server_public_IP}; # Please edit this part

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Update Nginx configuration
$ sudo vim /etc/nginx/nginx.conf

# Include site configuration by adding the following lines inside the http block
include /etc/nginx/sites-enabled/*;

sudo systemctl restart nginx.service

# Start the Flask app with Gunicorn
$ gunicorn -b 0.0.0.0:5000 random_rank:app &

# Test the application
$ curl 127.0.0.1
