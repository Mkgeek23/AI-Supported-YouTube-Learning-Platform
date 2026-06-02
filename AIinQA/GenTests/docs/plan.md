# YouTube Learning Platform Test Plan

## Overview
This document outlines the testing strategy for the YouTube Learning Platform application. The application consists of three main modules:
1. **Transcriber Module**: Handles YouTube video transcription
2. **Modules Module**: Structures transcripts into learning modules
3. **Quizzes Module**: Generates quiz questions for modules

The test plan aims to achieve comprehensive test coverage using Python's `unittest` framework, with appropriate mocking of external dependencies.

## Test Environment Setup

### Dependencies
- Python 3.8+
- unittest (standard library)
- unittest.mock (for mocking external dependencies)
- pytest (optional, for running tests with coverage reports)

### Test Database
- Use in-memory SQLite databases for testing to avoid affecting production data
- Create test fixtures to initialize database schemas and sample data

### External Dependencies Mocking
- Mock the Whisper model for transcription
- Mock the DeepSeek LLM model for module title generation
- Mock the Nebius API for quiz generation
- Mock YouTube download functionality

## Test Structure

### 1. Unit Tests

#### 1.1 Transcriber Module Tests
- **Database Operations**
  - Test `init_database()` creates the correct schema
  - Test `get_transcription_from_db()` retrieves correct data
  - Test `save_transcription_to_db()` saves data correctly

- **Transcription Function**
  - Test `transcribe_youtube_video()` with mocked dependencies
  - Test caching mechanism works correctly
  - Test error handling for invalid URLs
  - Test handling of different video formats

#### 1.2 Modules Module Tests
- **Database Operations**
  - Test `init_course_cache()` creates the correct schema
  - Test `get_cached_modules()` retrieves correct data
  - Test `save_modules_to_cache()` saves data correctly

- **Module Structuring**
  - Test `structure_transcript()` correctly divides content
  - Test `extract_video_id()` with various URL formats
  - Test caching mechanism works correctly

- **Title Generation**
  - Test `TitleGenerator` class with mocked model
  - Test `generate_module_title()` with various inputs
  - Test fallback mechanism when model fails

#### 1.3 Quizzes Module Tests
- **Database Operations**
  - Test `QuizCache` class initialization
  - Test `get_cached_quiz()` retrieves correct data
  - Test `save_quiz_to_cache()` saves data correctly

- **Quiz Generation**
  - Test `CourseDesignerAgent.generate_quiz_questions()` with mocked API
  - Test `get_quiz()` retrieves or generates correctly
  - Test `generate_all_module_quizzes()` for multiple modules
  - Test error handling and fallback mechanisms

- **Helper Functions**
  - Test `get_module_text()` extracts text correctly
  - Test `call_nebius_llm()` with mocked API
  - Test logging functionality

#### 1.4 Flask Application Tests
- Test route `/` returns correct template
- Test route `/modules` with valid and invalid parameters
- Test route `/generate_quiz` with valid and invalid parameters
- Test error handling in routes

### 2. Integration Tests

#### 2.1 Module Interactions
- Test transcriber → modules pipeline
- Test modules → quizzes pipeline
- Test full pipeline from video URL to quiz generation

#### 2.2 API Integration
- Test integration with YouTube API (with limited real calls)
- Test integration with LLM APIs (with limited real calls)

### 3. End-to-End Tests
- Test the complete workflow with mocked external services
- Verify the application handles real-world scenarios correctly

## Test Execution Plan

### Phase 1: Setup Test Environment
1. [x] Create test configuration
2. [x] Set up mock objects and fixtures
3. [x] Create helper functions for common test operations

### Phase 2: Implement Unit Tests
1. [x] Create test files for each module
   - [x] `test_transcriber.py`
   - [x] `test_modules.py`
   - [x] `test_quizzes.py`
   - [x] `test_main.py`
2. [x] Implement tests for each function in each module
3. [ ] Verify unit test coverage

### Phase 3: Implement Integration Tests
1. [x] Create integration test files
   - [x] `test_integration.py`
2. [x] Implement tests for module interactions
3. [ ] Verify integration test coverage

### Phase 4: Implement End-to-End Tests
1. [x] Create end-to-end test file
   - [x] `test_e2e.py`
2. [x] Implement full workflow tests
3. [ ] Verify end-to-end test coverage

### Phase 5: Verify and Optimize
1. Run all tests and verify passing status
2. Generate coverage reports
3. Identify and address any gaps in testing
4. Optimize tests for performance

## Test Coverage Goals
- Aim for at least 80% code coverage across all modules
- 100% coverage of critical paths and error handling
- Cover all edge cases identified during analysis

## Continuous Integration
- Configure tests to run automatically on code changes
- Set up coverage reporting in CI pipeline
- Enforce minimum coverage thresholds

## Maintenance
- Update tests when new features are added
- Refactor tests when code is refactored
- Review and improve tests periodically

## Conclusion
This test plan provides a comprehensive approach to testing the YouTube Learning Platform application. By following this plan, we can ensure the application functions correctly, handles errors gracefully, and maintains high quality as it evolves.
