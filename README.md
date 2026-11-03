# Flask Weather App

Search any city and see current weather plus a 5-day forecast.
Built with Python + Flask, using the free [Open-Meteo](https://open-meteo.com) API (no API key needed).

This README covers:

1. [Running the app on your own computer](#1-run-it-locally)
2. [Deploying it on AWS, step by step](#2-deploy-on-aws-ec2-step-by-step)
3. [Fixing common problems](#3-troubleshooting)

---

## Project structure

```
weather_app/
├── app.py              <- Flask backend
├── requirements.txt    <- Python packages the app needs
├── .gitignore          <- files Git should never upload
├── README.md           <- this file
└── templates/
    └── index.html      <- the web page (folder name MUST be "templates")
```

---

## 1. Run it locally

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

> Port 5001 is used because macOS often uses port 5000 for AirPlay.

---

## 2. Deploy on AWS (EC2), step by step

### What are we going to do?

AWS lets you rent a small computer in the cloud. That rented computer is called an **EC2 instance**.
We will:

1. Rent one (a Linux server).
2. Copy our app onto it.
3. Run the app with **Gunicorn** (a production-ready Python web server).
4. Put **Nginx** in front of Gunicorn so people on the internet can reach it on the normal web port (80).
5. Use **systemd** so the app starts automatically and restarts if it crashes.

```
Browser  ──>  Nginx (port 80)  ──>  Gunicorn (port 8000)  ──>  Your Flask app
```

Why not just run `python app.py` on the server? Because that is Flask's development server. It is not
built to handle real traffic safely, and `debug=True` can expose your code. Gunicorn + Nginx is the
standard setup.

### Before you start

You need:

- A computer with internet and a terminal (Terminal on Mac/Linux, PowerShell on Windows 10/11).
- An AWS account (Step 1).
- A debit/credit card (AWS asks for one to verify your account, even for free usage).
- Your project code on GitHub (recommended, Step 2) or ready to copy with `scp` (Step 7, Option B).

> **About cost:** New AWS accounts usually get some free usage or credits, but the rules change over time
> and differ by account. Check the **Billing** page in your AWS console and the
> [AWS Free Tier page](https://aws.amazon.com/free/) for what applies to you. A small instance left
> running can cost money after your free usage ends. **Always follow [Step 13](#step-13-clean-up-so-you-dont-get-billed)
> when you are done practicing.**

---

### Step 1: Create an AWS account and add safety nets

1. Go to https://aws.amazon.com and click **Create an AWS Account**. Follow the sign-up steps.
2. Sign in to the **AWS Management Console**.
3. In the top-right corner, choose a **Region** (the physical location of the server).
   Pick one close to your users. For India, choose **Asia Pacific (Mumbai) ap-south-1**.
   Use the same region for everything below, because resources in one region do not show up in another.
4. **Set a billing alert** so you never get a surprise bill:
   - Search for **Billing and Cost Management** in the top search bar.
   - Open **Budgets** and create a budget with a small amount (for example, $5) that emails you
     when you reach it.
5. Good habit: turn on **MFA** (multi-factor authentication) for your account. In the console, open the
   account menu in the top right, go to **Security credentials**, and add an MFA device
   (an authenticator app on your phone).

---

### Step 2: Prepare your code (put it on GitHub)

Putting the code on GitHub makes it very easy to copy to the server and to update later.

1. Make sure `requirements.txt` contains:
   ```
   Flask>=3.0
   requests>=2.31
   gunicorn>=22.0
   ```
2. Make sure you have the `.gitignore` file from this project. It stops secrets like `.pem` key files
   and the `venv` folder from being uploaded. **Never upload a `.pem` file to GitHub.**
3. Create a new repository on https://github.com (click **New**), then in your project folder run:
   ```bash
   git init
   git add .
   git commit -m "Weather app"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/weather_app.git
   git push -u origin main
   ```
   Replace `YOUR_USERNAME` with your GitHub username. Keep the repository **public** for the simplest
   setup (the server can then download it without a password).

---

### Step 3: Launch an EC2 instance (your server)

1. In the AWS console search bar, type **EC2** and open it.
2. Click the orange **Launch instance** button.
3. Fill in the form:

   | Field | What to choose |
   |-------|----------------|
   | **Name** | `weather-app-server` |
   | **Application and OS Images (AMI)** | **Ubuntu**, then **Ubuntu Server 24.04 LTS** (pick the one marked *Free tier eligible* if shown) |
   | **Instance type** | The smallest one marked *Free tier eligible* (usually `t2.micro` or `t3.micro`) |
   | **Key pair (login)** | Click **Create new key pair** (see below) |
   | **Network settings** | Click **Edit** and set up the firewall (see below) |
   | **Configure storage** | Leave the default (8 GiB) |

4. **Create the key pair.** This is your password file for logging in to the server.
   - Name: `weather-key`
   - Type: **RSA**
   - Format: **.pem** (Mac/Linux, and Windows 10/11 PowerShell)
   - Click **Create key pair**. A file called `weather-key.pem` downloads.
   - **Keep it safe.** AWS shows it only once. If you lose it you cannot log in with SSH.

5. **Set up the firewall (Security Group).** A security group decides who is allowed to talk to your
   server. In **Network settings** make sure these rules exist:
   - **Allow SSH traffic from: My IP.** This lets only your computer log in. (Avoid `Anywhere` here.)
   - Tick **Allow HTTP traffic from the internet.** This lets everyone open your website on port 80.

6. Click **Launch instance**. Then click **View all instances**. Wait until *Instance state* says
   **Running** and *Status check* says **2/2 checks passed** (about a minute).

7. Click your instance and copy the **Public IPv4 address** (for example `13.233.10.25`).
   This is your server's address on the internet.

---

### Step 4: Connect to your server

You have two ways. Pick one.

#### Option A: Browser (easiest, no key file needed)

1. In the EC2 console, select your instance and click **Connect** (top).
2. Choose the **EC2 Instance Connect** tab and click **Connect**.
3. A terminal opens in your browser. You are in.

> If this fails, your security group's SSH rule probably does not allow your current IP. See
> [Troubleshooting](#3-troubleshooting).

#### Option B: SSH from your own terminal

**Mac / Linux:**
```bash
cd ~/Downloads                       # wherever weather-key.pem is
chmod 400 weather-key.pem            # SSH refuses keys that other users can read
ssh -i weather-key.pem ubuntu@YOUR_PUBLIC_IP
```

**Windows (PowerShell):**
```powershell
cd $HOME\Downloads
ssh -i weather-key.pem ubuntu@YOUR_PUBLIC_IP
```

The first time, it asks *"Are you sure you want to continue connecting?"* Type `yes` and press Enter.
Ubuntu servers always use the username **`ubuntu`**.

When you see a prompt like `ubuntu@ip-172-31-...:~$` you are inside your server.
**All commands from here on are typed on the server.**

---

### Step 5: Install the software

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git
```

- `sudo` means "run as administrator".
- `apt` is Ubuntu's app installer.
- If a purple screen asks about restarting services, press Enter to accept the defaults.

---

### Step 6: Get your code onto the server

#### Option A: From GitHub (recommended)

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/weather_app.git
cd weather_app
ls
```

You should see `app.py`, `requirements.txt` and `templates`.

#### Option B: Copy from your computer with `scp`

Run this on **your own computer** (not the server), from the folder that contains `weather_app`:

```bash
scp -i ~/Downloads/weather-key.pem -r weather_app ubuntu@YOUR_PUBLIC_IP:~/
```

---

### Step 7: Set up Python and test the app

On the server:

```bash
cd ~/weather_app
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

A **venv** (virtual environment) keeps this project's packages separate from the rest of the system.

Now test that Gunicorn can run your app:

```bash
gunicorn --bind 127.0.0.1:8000 app:app
```

`app:app` means "in the file `app.py`, use the variable named `app`".
If you see `Listening at: http://127.0.0.1:8000`, it works. Press **Ctrl + C** to stop it.
(You can't open it in a browser yet. Nginx comes in Step 9.)

---

### Step 8: Make the app run in the background (systemd)

Right now the app stops when you close the terminal. We fix that by creating a **service**.

Run Gunicorn WSGI server to serve the Flask Application When you “run” flask, you are actually running Werkzeug’s development WSGI server, which forward requests from a web server. Since Werkzeug is only for development, we have to use Gunicorn, which is a production-ready WSGI server, to serve our application.

Install Gunicorn using the below command:

```
pip install gunicorn
```
Gunicorn is running (Ctrl + C to exit gunicorn)!

Use systemd to manage Gunicorn Systemd is a boot manager for Linux. We are using it to restart gunicorn if the EC2 restarts or reboots for some reason. We create a .service file in the /etc/systemd/system folder, and specify what would happen to gunicorn when the system reboots. We will be adding 3 parts to systemd Unit file — Unit, Service, Install

Unit — This section is for description about the project and some dependencies Service — To specify user/group we want to run this service after. Also some information about the executables and the commands. Install — tells systemd at which moment during boot process this service should start. With that said, create an unit file in the /etc/systemd/system directory


1. Create the service file:
   ```bash
   sudo nano /etc/systemd/system/weather_app.service
   ```
2. Paste this in:
   ```ini
   [Unit]
   Description=Gunicorn server for the Flask weather app
   After=network.target

   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/home/ubuntu/weather_app
   ExecStart=/home/ubuntu/weather_app/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Save and exit nano: press **Ctrl + O**, then **Enter**, then **Ctrl + X**.

4. (enable the service:)Start it and make it start on every reboot:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start weather_app
   sudo systemctl enable weather_app
   sudo systemctl status weather_app
   ```
   You should see **active (running)** in green. Press **q** to leave the status screen.

> Check if the app is running with

```
curl localhost:8000
```

---

### Step 9: Set up Nginx (the front door)

Run Nginx Webserver to accept and route request to Gunicorn Finally, we set up Nginx as a reverse-proxy to accept the requests from the user and route it to gunicorn.

Install Nginx

```
sudo apt-get nginx
```

Start the Nginx service and go to the Public IP address of your EC2 on the browser to see the default nginx landing page

```
sudo systemctl start nginx
sudo systemctl enable nginx

```

1. Create the Nginx config:
   Edit the default file in the sites-available folder.
   
   ```bash 
   sudo nano /etc/nginx/sites-available/weather_app
   ```
2. Paste this in:
   Add the following code at the top of the file (below the default comments)
   ```nginx
   server {
       listen 80;
       server_name _;
   ```

   Add a proxy_pass to flaskhelloworld atlocation /

   ```nginx
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   This says: "Take any request that arrives on port 80 and pass it to Gunicorn on port 8000."
3. Save and exit (**Ctrl + O**, **Enter**, **Ctrl + X**).
4. Turn the config on and remove Nginx's default welcome page:
   ```bash
   sudo ln -s /etc/nginx/sites-available/weather_app /etc/nginx/sites-enabled/
   sudo rm /etc/nginx/sites-enabled/default
   ```
5. Check for typos, then restart Nginx:
   ```bash
   sudo nginx -t

   # restart Nginx
   sudo systemctl restart nginx
   ```
   `nginx -t` should print `syntax is ok` and `test is successful`.

---

### Step 10: Open your app

In your browser, go to:

```
http://YOUR_PUBLIC_IP
```

Use **http**, not https (HTTPS is an optional extra, see Step 14). Search for a city. You are live! 🎉

<img width="1268" height="773" alt="image" src="https://github.com/user-attachments/assets/b31875ee-3b77-48be-9422-c4810d0cf34b" />


---

### Step 11: Updating your app later

When you change your code:

1. On your computer: `git add .`, `git commit -m "your message"`, `git push`.
2. On the server:
   ```bash
   cd ~/weather_app
   git pull
   source venv/bin/activate
   pip install -r requirements.txt     # only matters if you added packages

   sudo systemctl restart weather_app
   ```

---

### Step 12: Useful commands

| What you want | Command |
|---------------|---------|
| See if the app is running | `sudo systemctl status weather_app` |
| See the app's error logs | `sudo journalctl -u weather_app -n 50 --no-pager` |
| Restart the app | `sudo systemctl restart weather_app` |
| See Nginx error logs | `sudo tail -n 50 /var/log/nginx/error.log` |
| Restart Nginx | `sudo systemctl restart nginx` |

---

### Step 13: Clean up so you don't get billed

When you no longer need the server:

1. EC2 console, **Instances**, select your instance.
2. **Instance state**, then **Terminate (delete) instance**, then confirm.
3. Wait until the state says **Terminated**.
4. Check **Billing** a day later to confirm nothing is still being charged.

Good to know:

- **Stop** pauses the server but you still pay for its storage, and the public IP **changes** when you start it again.
- **Terminate** deletes it for good.
- A public IP that stays the same forever needs an **Elastic IP** (EC2 console, **Elastic IPs**). Release it when
  you are done, because an unused Elastic IP can cost money.

---

### Step 14: Optional next steps

- **Your own domain name:** Buy a domain (Route 53 or any registrar), then point an **A record** at your
  server's Elastic IP. Change `server_name _;` in the Nginx file to `server_name yourdomain.com;`.
- **HTTPS (the padlock):** With a domain pointing at your server, run:

   ```bash
  sudo apt install -y certbot python3-certbot-nginx
  sudo certbot --nginx -d yourdomain.com
  ```

  Also add an **HTTPS (port 443)** inbound rule to your security group.
- **Easier hosting later:** AWS Elastic Beanstalk can run Flask apps with less manual setup. Doing it by hand
  first, as above, teaches you what is happening underneath.

---

## 3. Troubleshooting

| Problem | Likely cause and fix |
|---------|----------------------|
| Browser says the site **can't be reached / times out** | The security group is missing the HTTP rule. EC2, your instance, **Security** tab, security group, **Edit inbound rules**, add **HTTP, port 80, source 0.0.0.0/0**. Also check you used `http://`, not `https://`. |
| **502 Bad Gateway** | Nginx is working but Gunicorn is not. Run `sudo systemctl status weather_app` and `sudo journalctl -u weather_app -n 50 --no-pager` to see the error. |
| **Welcome to nginx!** page | You skipped `sudo rm /etc/nginx/sites-enabled/default`. Run it, then `sudo systemctl restart nginx`. |
| `jinja2.exceptions.TemplateNotFound` | `index.html` must be inside a folder named exactly `templates`, next to `app.py`. |
| `Permission denied (publickey)` when using SSH | Wrong username (use `ubuntu`), wrong key file, or you skipped `chmod 400 weather-key.pem`. |
| SSH or Instance Connect times out | Your home IP changed. Edit the security group's SSH rule and set the source to **My IP** again. |
| `WARNING: UNPROTECTED PRIVATE KEY FILE` | Run `chmod 400 weather-key.pem`. |
| `ModuleNotFoundError: No module named 'flask'` | The venv isn't active or packages aren't installed. Run `source venv/bin/activate` then `pip install -r requirements.txt`. |
| App loads but shows "weather service didn't respond" | The server can't reach the internet API. Check the instance has a public IP and the security group's **outbound** rules still allow all traffic (the default). |
| Changes don't show after `git pull` | You forgot `sudo systemctl restart weather_app`. |

---

## Glossary 

- **AWS:** Amazon's cloud platform, where you rent computers and services.
- **EC2:** AWS's "rent a virtual computer" service.
- **Instance:** One rented virtual computer.
- **AMI:** The starting template for the computer (the operating system, for example Ubuntu).
- **Key pair / .pem file:** Your private key for logging in. Treat it like a password.
- **Security group:** A firewall that controls which ports are open to whom.
- **Port:** A numbered door on a server. 22 = SSH, 80 = HTTP, 443 = HTTPS.
- **SSH:** A secure way to control a server from your terminal.
- **Gunicorn:** A server that runs Python web apps reliably.
- **Nginx:** A web server that receives internet traffic and passes it to Gunicorn.
- **systemd:** Linux's tool for running programs in the background and restarting them.
- **venv:** A private folder of Python packages for one project.
