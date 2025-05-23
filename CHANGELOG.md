# Changelog

All notable changes to the Quick Understand application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2024-07-16

### Added
- Add pandas dependency and refactor document processing in API
- Implement cookie-less session management and user ID handling for Hugging Face Spaces compatibility
- Add logging configuration and integrate logging into API endpoints

### Changed
- Refactor Qdrant integration and update dependencies
- Refactor LangSmith run logging to use updated API methods
- Enhance Dockerfile and application configuration for improved functionality
- Add non-root user and update permissions in Dockerfile
- Update Dockerfile to improve application structure and logging
- Enhance Qdrant collection management with error handling and async support
- Remove version specification from docker-compose.yml for Qdrant service integration

## [0.3.0] - 2025-04-13

### Added
- Docker deployment support with multi-stage build
- Fixed linting errors in chat router
- Improved error handling for session validation
- Enhanced chat history management
- Better documentation in code comments

### Changed
- Updated all Python dependencies to latest versions
- Improved Docker container efficiency
- Enhanced user experience with cleaner UI
- Fixed streaming response formatting

## [0.2.0] - 2024-06-14

### Added
- Response streaming for real-time AI answers
- Improved font readability with better typography
- Dark mode support with darker header in dark theme
- Version information in application footer
- API version endpoint

### Changed
- Renamed application to "Quick Understand"
- Enhanced message display with better formatting
- Fixed duplicate message issues in streaming responses
- Improved code block styling

## [0.1.0] - 2024-06-01

### Added
- Initial release of RAG Chat application
- Document upload and processing
- Question answering using RAG approach
- Basic UI with chat interface
- Quiz generation feature
- Document summary visualization 