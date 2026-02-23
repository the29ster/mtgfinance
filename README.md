# MTGFinance

MTGFinance is a full-stack Django web application that tracks and visualizes *Magic: The Gathering* card prices over time. It combines real-time pricing data from the Scryfall API with large-scale historical datasets from MTGJSON to provide searchable cards and interactive price history charts.

## Overview

This project was built to address a key limitation in existing MTG pricing tools: most APIs only provide current prices. MTGFinance aggregates and stores historical pricing data, enabling users to analyze long-term trends and make more informed decisions.

## Features

- 🔍 Card search powered by the Scryfall API  
- 📈 Historical price tracking using MTGJSON data  
- 📊 Interactive price history visualizations  
- 🗄️ PostgreSQL-backed database for scalable storage  
- 🐳 Dockerized development environment  

## Tech Stack

- **Backend:** Python, Django  
- **Database:** PostgreSQL  
- **Data Sources:** Scryfall API, MTGJSON  
- **DevOps:** Docker  
- **Frontend:** HTML, CSS, JavaScript  

## Key Engineering Work

- Designed and implemented a relational database schema for storing large-scale historical pricing data  
- Built a data ingestion pipeline to process and import MTGJSON datasets efficiently  
- Optimized query performance for retrieving time-series data used in visualizations  
- Ensured consistent development environments using Docker  

## Purpose

This project demonstrates full-stack development, data engineering, and performance optimization skills by solving a real-world problem involving large datasets and time-series analysis.
