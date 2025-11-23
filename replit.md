# Free Fire Token Generator Service

## Overview
This project is a Flask API service designed to provide Free Fire game-like bot functionality with multi-server support and encrypted communication. Its primary purpose is to automatically generate and manage authentic JWT tokens for multiple game accounts across different regions (India, US/NX, AG). The service aims for a fully built-in, automated solution without requiring a web dashboard interface, focusing on reliable token generation, efficient "like" sending, and robust error handling. The business vision is to provide a scalable and high-performance backend for Free Fire bot operations.

## User Preferences
- Non-technical user requiring simple explanations
- Focus on functionality over technical details
- Prefers automatic solutions over manual interventions
- Wants everything built-in without web dashboard interface
- Prefers automatic background operation

## System Architecture
The core of the system is a Flask API (`main.py`) which provides various endpoints for game interactions. Token management is handled by generating real JWT tokens for all configured accounts across servers (IND, NX, AG) every 6 hours, storing them in region-specific JSON files (`data/tokens/`). Account credentials, encrypted, are stored in `IND_ACC.json`, `NX_ACC.json`, and `AG_ACC.json`. The service utilizes AES encryption and protobuf for secure communication and data handling. The system uses internal JSON-based storage for player records with automatic token generation. The system is designed for high performance with parallel processing for ultra-fast token generation and controlled concurrency for API requests. UI/UX considerations include clear API responses with perfect Unicode handling for player nicknames and a professional landing page for API documentation.

Key architectural decisions and features include:
- **Main Application**: Flask API for all service operations.
- **Token Management**: Scheduled real JWT token generation every 6 hours, saved to `data/tokens/` directory. Each region (IND, NX, AG) tracks its generation time independently to prevent unnecessary regeneration.
- **Encryption**: AES encryption and protobuf handling for secure data.
- **Storage**: Internal JSON-based storage for player records (lightweight and fast).
- **Multi-server Support**: Configured for IND, NX, and AG regions, with specific server URLs.
- **High Performance**: 15x speed improvement in token generation with parallel processing and optimized like sending.
- **Robustness**: Enhanced error handling, multiple fallback mechanisms, and rate limiting with semaphore control. Includes intelligent retry logic for requests ensuring a high success rate.
- **API Endpoints**: Comprehensive set of API endpoints for `/like`, `/records`, `/tokens`, `/bio`, `/token`, `/accesstok`, `/visit`, and more, each with clear documentation and standardized response formats.
- **Protobuf Integration**: Extracted and integrated various protobuf files for specific functionalities like JWT generation and bio updates.
- **Helper Modules**: `bio_jwt_helper.py` for JWT generation from different credentials and bio update workflows.
- **Account Structure**: Encrypted guest account credentials for token generation across all regions.
- **Daily Token Usage Limit**: Each token is limited to 20 requests per day, with automatic daily resets, to ensure fair distribution and prevent exhaustion.
- **Discord Webhook Integration**: For real-time monitoring of token generation events and system status.

## External Dependencies
- **Gunicorn**: Production-ready WSGI HTTP server for deploying the Flask application.
- **Protobuf (Google Protocol Buffers)**: For serializing structured data, used in Free Fire API communication and JWT generation.
- **PyCryptodome**: Python library providing cryptographic recipes, used for AES encryption.
- **Requests / Aiohttp**: HTTP libraries for making requests to the Free Fire API.
- **Schedule**: Python library for scheduling periodic tasks, used for token regeneration.