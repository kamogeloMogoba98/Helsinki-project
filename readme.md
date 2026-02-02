# Helsinki Live Transit: End-to-End IoT Data Engineering Pipeline

This project demonstrates a **production-grade data engineering pipeline** that ingests real-time MQTT streams from **Helsinki’s public transport system**, processes them via a **FastAPI backend on AWS EC2**, and stores historical data in an **Amazon S3 Data Lake** for **serverless analytics using Amazon Athena** and **visualization in Power BI**.

---

## Overall Data Engineering Architecture

This diagram provides a high-level view of the end-to-end data flow, from real-time vehicle telemetry to analytics and visualization.

Insert overall architecture diagram here

```text
images/architecture-overview.png


Pipeline Flow:
MQTT (IoT Source) → EC2 Ingestion & Processing → S3 Data Lake → Athena Tables & Views → Power BI

Ingestion Layer Architecture (MQTT → EC2)

This section focuses on real-time ingestion, showing how vehicle telemetry is securely consumed and processed.

Insert MQTT ingestion architecture diagram here

images/mqtt-to-ec2.png


Key Details

Protocol: MQTT over WSS / SSL

Source: HSL (Helsinki Regional Transport Authority) live positioning feed

Compute: Amazon EC2

Process:

Python-based MQTT subscriber

FastAPI backend for real-time SSE streaming

Amazon EC2 Instance Configuration

This diagram or screenshot highlights the EC2 instance setup, networking, and runtime environment.

Insert EC2 instance screenshot here

images/ec2.png


EC2 Responsibilities

Hosts the FastAPI application

Runs MQTT ingestion (producer.py)

Streams real-time data to the frontend

Batches and writes data to Amazon S3

Storage Layer – Amazon S3 Data Lake Architecture

This diagram shows how raw and processed data is organized in the S3 Data Lake.

Insert S3 data lake architecture diagram here

images/s3.png


Storage Design

Partitioned by date and time

Optimized for Athena querying

Supports Parquet / CSV formats

Example structure:

s3://helsinki-transit-data/
 ├── raw/
 │   └── year=2026/month=01/day=25/
 └── processed/
     └── year=2026/month=01/day=25/

Analytics Layer – Athena Tables and Views

This section documents the logical analytics layer built on top of S3.

Athena Table Definitions

Insert Athena tables screenshot here

images/Athena.png


External tables mapped directly to S3

Schema-on-read

Partition pruning for performance

Athena Views

Insert Athena views screenshot here

images/athena-views.png


Aggregated vehicle movement

Congestion analysis

Time-windowed summaries

Visualization Layer – Power BI Integration

This diagram shows how Power BI connects to Athena for analytics and reporting.

Insert Power BI architecture or dashboard image here

images/powerbi-dashboard.png


Power BI Features

DirectQuery / ODBC connection to Athena

Real-time and historical analysis

Route performance and congestion dashboards

Project UI and Results
Real-Time Map (FastAPI and Leaflet.js)

Insert real-time map UI screenshot here

images/realtime-map.png


Server-Sent Events (SSE)

Near real-time vehicle updates

Interactive Leaflet.js map

Tech Stack
Languages and Frameworks

Python (FastAPI, Pandas, Paho-MQTT)

AWS Services

Amazon EC2

Amazon S3

Amazon Athena

AWS IAM

DevOps and Tooling

nohup for background processing

requirements.txt for dependency management

Frontend and BI

HTML5

Leaflet.js

Power BI Desktop

Deployment Overview

Provision EC2

Amazon Linux 2

Open ports: 80, 8000, 443

Configure Ingestion

Run producer.py for MQTT ingestion

Enable batching to S3

Create Athena Tables and Views

Point to S3 Data Lake

Enable partitioning

Connect Power BI

Use Athena connector

Build dashboards

Repository Structure
├── main.py            # FastAPI streaming backend
├── producer.py        # MQTT ingestion and S3 persistence
├── index.html         # Live Leaflet.js frontend
├── images/            # Architecture diagrams and screenshots
│   ├── architecture-overview.png
│   ├── mqtt-to-ec2.png
│   ├── ec2-instance.png
│   ├── s3-data-lake.png
│   ├── athena-tables.png
│   ├── athena-views.png
│   ├── powerbi-dashboard.png
│   └── realtime-map.png
├── requirements.txt
└── README.md
