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

### Phase 1: Environment Preparation
1. **Dependency Installation**: Ensure `pytest`, `pytest-cov`, and other project requirements are installed. ✓
2. **Path Configuration**: Set `PYTHONPATH` to include the `AIinQA/GenTests` directory to ensure modules are discoverable. ✓

### Phase 2: Codebase Analysis and Fixes
1. **Fix Existing Tests**: Address the identified failures in `test_*_junie.py` files. ✓
   - Resolved `sqlite3.OperationalError` by making database paths configurable in `quizzes.py`. ✓
   - Fixed assertion errors in `test_main_junie.py`, `test_modules_junie.py`, and `test_quizzes_junie.py`. ✓
2. **Refine Mocks**: Ensure all external API calls (Whisper, Nebius LLM, YouTube) are consistently and correctly mocked across all test suites. ✓

### Phase 3: Implementing Full Coverage Unit Tests
1. **Transcriber Module (`transcriber.py`)**:
   - Test all database operations (init, get, save). ✓
   - Test `transcribe_youtube_video` with various scenarios (success, failure, cache hit/miss). ✓
   - Test helper functions and error handling. ✓
2. **Modules Module (`modules.py`)**:
   - Test `extract_video_id` with different YouTube URL formats. ✓
   - Test `TitleGenerator` and `generate_module_title`. ✓
   - Test `structure_transcript` logic. ✓
   - Test database caching. ✓
3. **Quizzes Module (`quizzes.py`)**:
   - Test `CourseDesignerAgent` methods. ✓
   - Test `get_quiz` and `generate_all_module_quizzes`. ✓
   - Test `QuizCache` operations. ✓
   - Test Nebius LLM integration mocking. ✓
4. **Main Module (`main.py`)**:
   - Test all Flask routes (`/`, `/modules`, `/generate_quiz`). ✓
   - Test input validation and error responses. ✓

### Phase 4: Integration and End-to-End Testing
1. **Integration Tests**:
   - Verify the flow between Transcriber -> Modules. ✓
   - Verify the flow between Modules -> Quizzes. ✓
2. **E2E Tests**:
   - Simulate a full user journey from video URL submission to quiz generation using the Flask test client. ✓

### Phase 5: Verification and Finalization
1. **Coverage Analysis**: Run `pytest --cov=.` to verify that at least 80% coverage is achieved for each module. ✓
   - Total coverage reached: **96%**. ✓
2. **Refactoring**: Clean up test code, remove redundancies, and ensure tests are fast and reliable. ✓
3. **Documentation**: Final test plan updated. ✓

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
