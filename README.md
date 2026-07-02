# 🛡️ Dockerized Nginx WAF & SOC Pipeline

> An industrial-grade Web Application Firewall (WAF) deployment using Nginx, ModSecurity, and the OWASP Core Rule Set (CRS). This project features a fully Dockerized Security Operations Center (SOC) logging pipeline using Grafana and Loki to visualize blocked attacks in real time.

---

## 📖 Table of Contents

- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start Deployment](#-quick-start-deployment)
- [⚔️ Testing the WAF (Proof of Concept)](#️-testing-the-waf-proof-of-concept)
- [📊 Visualizing Attacks (Grafana SOC)](#-visualizing-attacks-grafana-soc)
- [🛠️ Configuration Details](#️-configuration-details)
- [🛑 Teardown](#-teardown)

---

## 🏗️ Architecture

Traffic flows through the Nginx reverse proxy, where the ModSecurity engine evaluates HTTP requests against the OWASP Core Rule Set (CRS). Malicious requests are blocked (`403 Forbidden`) and logged. Promtail reads these logs and ships them to Loki, which Grafana queries to visualize attack activity in real time.

```text
[ Attacker / User ]
        │
        ▼ (Port 80)
┌────────────────────────────────────────┐
│             Nginx Reverse Proxy        │
│  ┌──────────────────────────────────┐  │      [ SOC Logging Pipeline ]
│  │ ModSecurity WAF Engine           │  │ ──┐   ┌──────────┐    ┌─────────┐    ┌─────────┐
│  │ (OWASP Core Rule Set)            │  │   ├──▶│ Promtail │──▶│  Loki   │──▶│ Grafana │
│  └──────────────────────────────────┘  │ ──┘   └──────────┘    └─────────┘    └─────────┘
└────────────────────────────────────────┘
        │ (Clean Traffic Only)
        ▼ (Port 3000)
┌────────────────────────────────────────┐
│            Vulnerable Web App          │
│            (OWASP Juice Shop)          │
└────────────────────────────────────────┘
```

---

## 🚀 Quick Start Deployment

### Prerequisites

Ensure you have the following installed:

- Docker
- Docker Compose

### Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/industrial-waf-project.git
cd industrial-waf-project
```

### Launch the Infrastructure

```bash
docker-compose up -d
```

### Verify Services

| Service | URL |
|---------|-----|
| OWASP Juice Shop | http://localhost |
| Grafana Dashboard | http://localhost:3000 |

> **Note:** No password is required for Grafana in this development environment.

---

## ⚔️ Testing the WAF (Proof of Concept)

This repository includes a Python script that automatically tests whether the WAF correctly blocks malicious payloads.

### Run the Attack Script

```bash
python3 attack-scripts/test_waf.py
```

### Expected Results

#### ✅ Benign Traffic

The script requests the homepage.

**Expected Result**

```text
HTTP 200 OK
```

Traffic is successfully forwarded to OWASP Juice Shop.

---

#### 🚫 SQL Injection (SQLi)

The script attempts to bypass authentication using:

```text
admin@juice-sh.op' OR 1=1--
```

**Expected Result**

```text
HTTP 403 Forbidden
```

ModSecurity detects and blocks the attack.

---

#### 🚫 Cross-Site Scripting (XSS)

The script attempts to inject a malicious script tag.

**Expected Result**

```text
HTTP 403 Forbidden
```

The request is blocked by the OWASP Core Rule Set.

---

## 📊 Visualizing Attacks (Grafana SOC)

> 📸 Consider adding a screenshot of your Grafana dashboard here.

### Steps

1. Open Grafana:

   ```
   http://localhost:3000
   ```

2. Navigate to:

   ```
   Connections → Data Sources
   ```

3. Add a new **Loki** data source.

4. Configure the URL:

   ```text
   http://loki:3100
   ```

5. Click **Save & Test**.

6. Navigate to the **Explore** tab.

7. Run the following LogQL query:

```logql
{job="modsecurity"}
```

You should see a real-time stream of blocked attacks, including:

- Source IP address
- Attack payload
- Triggered OWASP CRS rule
- Timestamp
- HTTP status

---

## 🛠️ Configuration Details

| Component | Configuration |
|-----------|---------------|
| WAF Engine | OWASP ModSecurity Core Rule Set (CRS) v3.3 |
| Paranoia Level | 2 |
| Logging | ModSecurity writes to `error.log` |
| Log Collection | Promtail scrapes logs from a shared Docker volume |
| Visualization | Grafana queries Loki for real-time dashboards |

### Security Configuration

- **Paranoia Level:** `2`

This provides stronger protection by enabling stricter OWASP CRS rules while maintaining a practical balance between security and false positives for typical web applications.

### Log Routing

ModSecurity writes its logs to a shared Docker volume.

Promtail mounts this volume as **read-only**, continuously scraping the logs and forwarding them to Loki for indexing and visualization.

---

## 🛑 Teardown

To stop and remove all containers, networks, and volumes:

```bash
docker-compose down -v
```

---

## 📄 License

Created for portfolio and educational demonstration purposes.
