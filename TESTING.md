# Testing Guidelines for gh-sync-labels

## Overview

This document describes the testing strategy and structure for the `gh-sync-labels` project. The test suite ensures reliability, maintainability, and correctness of the label synchronization functionality.

## Test Structure

```
tests/
├── unit/
│   ├── github_client_test.go
│   ├── csv_parser_test.go
│   ├── label_model_test.go
│   ├── sync_logic_test.go
│   └── cli_parser_test.go
├── integration/
│   ├── dry_run_test.go
│   ├── export_test.go
│   └── error_handling_test.go
├── fixtures/
│   ├── sample_labels.csv
│   ├── invalid_colors.csv
│   ├── missing_columns.csv
│   └── empty.csv
└── testdata/
    └── mock_responses.go
```

## Running Tests

### Run all tests
```bash
go test ./...
```

### Run specific test package
```bash
go test ./internal/github
```

### Run specific test function
```bash
go test -run TestCreateLabel ./...
```

### Run with verbose output
```bash
go test -v ./...
```

### Run with coverage report
```bash
go test -cover ./...
```

### Generate detailed coverage report
```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### Run tests with race detector
```bash
go test -race ./...
```

### Run benchmarks
```bash
go test -bench=. ./...
```

## Test Coverage Goals

- **Unit Tests**: Minimum 85% coverage
- **Integration Tests**: Critical user workflows
- **Overall Target**: 80% code coverage

## Unit Tests

### GitHub Client Tests (`github_client_test.go`)
- ✅ Initialization with valid GitHub CLI
- ✅ `ListLabels()` - Mock successful API response
- ✅ `CreateLabel()` - Mock label creation with all fields
- ✅ `UpdateLabel()` - Mock label update
- ✅ `DeleteLabel()` - Mock label deletion
- ✅ `Run()` method with dry-run flag
- ✅ Error handling for failed API calls
- ✅ Repository validation
- ✅ GitHub CLI availability check

### CSV Parser Tests (`csv_parser_test.go`)
- ✅ Valid CSV file parsing
- ✅ Missing required columns (name, color)
- ✅ Invalid color format (not hex)
- ✅ Empty CSV file
- ✅ Duplicate label names handling
- ✅ Special characters in descriptions
- ✅ Unicode support (emojis, etc.)
- ✅ Large CSV files
- ✅ Different line endings (CRLF, LF)

### Label Model Tests (`label_model_test.go`)
- ✅ Label creation with all fields
- ✅ Label creation with minimal fields
- ✅ Label validation (color format, name length)
- ✅ Label comparison and equality
- ✅ Color normalization (case-insensitive)
- ✅ Description truncation
- ✅ Label marshaling/unmarshaling

### Sync Logic Tests (`sync_logic_test.go`)
- ✅ Synchronize new labels (create operations)
- ✅ Update existing labels (detect differences)
- ✅ Skip unchanged labels
- ✅ Delete labels with `--prune` flag
- ✅ Combine multiple operations in one run
- ✅ Handle conflicts gracefully
- ✅ Preserve label order
- ✅ Dry-run simulation (no mutations)

### CLI Parser Tests (`cli_parser_test.go`)
- ✅ Default arguments parsing
- ✅ `--dry-run` flag parsing
- ✅ `--export` with filename
- ✅ `--repo` with custom repository
- ✅ `--overwrite` flag
- ✅ `--prune` flag
- ✅ `--config` with file path
- ✅ Invalid argument combinations
- ✅ Required arguments validation
- ✅ Help text generation

## Integration Tests

### Dry-Run Tests (`dry_run_test.go`)
- ✅ Verify no mutations occur during dry-run
- ✅ Verify read operations still work (ListLabels)
- ✅ Verify logging output contains "[DRY-RUN]" prefix
- ✅ Simulate full workflow with dry-run
- ✅ Verify output shows what would happen
- ✅ Compare dry-run output with actual run (same operations)

### Export Tests (`export_test.go`)
- ✅ Export labels to CSV file
- ✅ Verify CSV format and structure
- ✅ All labels exported correctly
- ✅ Special characters in output (preserved)
- ✅ File permissions (readable)
- ✅ Append vs. overwrite behavior
- ✅ Export with zero labels

### Error Handling Tests (`error_handling_test.go`)
- ✅ Invalid repository name
- ✅ GitHub CLI not installed
- ✅ GitHub CLI authentication failure
- ✅ Permission denied errors (insufficient access)
- ✅ Network errors (timeout, connection refused)
- ✅ Malformed CSV files
- ✅ File not found errors
- ✅ Graceful error messages and logging
- ✅ Partial failure recovery (continue on non-critical errors)

## Test Fixtures

### Sample CSV Files

**fixtures/sample_labels.csv** - Valid test data
```csv
name;color;description
bug;D73A4A;🐞 A bug that needs to be fixed.
feature;1D76DB;✨ A new function or feature.
documentation;0075CA;📚 Improvements or additions to documentation.
help wanted;008672;👋 This issue or pull request could use community input.
```

**fixtures/invalid_colors.csv** - Invalid hex colors
```csv
name;color;description
bug;GGGGGG;Invalid hex color
feature;D73A4;Too short hex
```

**fixtures/missing_columns.csv** - Missing required fields
```csv
name;description
bug;A bug that needs fixing
```

**fixtures/empty.csv** - Empty file (header only)
```csv
name;color;description
```

## Best Practices

### 1. Use Table-Driven Tests

```go
func TestLabelColorValidation(t *testing.T) {
    tests := []struct {
        name    string
        color   string
        wantErr bool
    }{
        {"valid color", "D73A4A", false},
        {"invalid hex", "GGGGGG", true},
        {"too short", "D73A4", true},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateColor(tt.color)
            if (err != nil) != tt.wantErr {
                t.Errorf("ValidateColor() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

### 2. Mock External Dependencies

```go
type MockGitHubClient struct {
    mock.Mock
}

func (m *MockGitHubClient) ListLabels(ctx context.Context) ([]Label, error) {
    args := m.Called(ctx)
    return args.Get(0).([]Label), args.Error(1)
}
```

### 3. Use Context for Timeouts

```go
func TestWithTimeout(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    result, err := client.ListLabels(ctx)
    // assertions
}
```

### 4. Clear Test Naming

- ✅ `TestCreateLabelWithValidData`
- ✅ `TestSyncLabelsHandlesDuplicates`
- ❌ `TestCreate`
- ❌ `TestSync`

### 5. Arrange-Act-Assert Pattern

```go
func TestExample(t *testing.T) {
    // Arrange: Set up test data
    label := &Label{
        Name:  "bug",
        Color: "D73A4A",
    }
    
    // Act: Perform the action
    err := client.CreateLabel(context.Background(), label)
    
    // Assert: Verify the result
    if err != nil {
        t.Fatalf("CreateLabel() error = %v", err)
    }
}
```

### 6. Test Error Cases

```go
func TestErrorHandling(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        wantErr string
    }{
        {"invalid repo", "invalid//repo", "invalid repository format"},
        {"empty config", "", "config file required"},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := Parse(tt.input)
            if err == nil || !strings.Contains(err.Error(), tt.wantErr) {
                t.Errorf("expected error containing %q, got %v", tt.wantErr, err)
            }
        })
    }
}
```

## Continuous Integration

GitHub Actions workflow (`.github/workflows/tests.yml`):
- Runs on push to main and pull requests
- Tests on Go 1.20+
- Generates coverage reports
- Runs race detector
- Checks code formatting
- Runs linters

## Code Coverage Requirements

- New code must maintain or improve overall coverage
- Coverage threshold: 80% minimum
- Critical paths: 90% coverage
- External API interactions: Mocked for unit tests

## Running Tests Locally

### Quick Test
```bash
make test
```

### Full Test Suite with Coverage
```bash
make test-coverage
```

### Test with Race Detector
```bash
make test-race
```

### Generate Coverage Report
```bash
make coverage-report
```

## Contributing Tests

When adding new features:

1. **Write tests first** (TDD recommended)
   ```bash
   go test -v ./internal/yourpackage -run TestNewFeature
   ```

2. **Ensure all tests pass locally**
   ```bash
   go test -race ./...
   ```

3. **Maintain or improve code coverage**
   - Check coverage: `go test -cover ./...`
   - Generate report: `go tool cover -html=coverage.out`

4. **Document complex test scenarios**
   - Add comments explaining why test is needed
   - Explain any mocking strategy

5. **Update this file** with new test patterns or guidelines

## Troubleshooting

### Tests fail locally but pass in CI
- Check Go version: `go version`
- Ensure all dependencies installed: `go mod tidy`
- Check for timing-related issues with race detector
- Verify environment variables (GITHUB_TOKEN, etc.)

### Coverage gaps
- Run with `go tool cover -html=coverage.out`
- Open `coverage.out` in browser to visualize
- Focus on uncovered branches first
- Add edge case tests

### Slow tests
- Check for unnecessary file I/O
- Use table-driven tests instead of separate functions
- Consider using `t.Parallel()` for independent tests
- Profile with `go test -cpuprofile=cpu.prof -memprofile=mem.prof ./...`

### Flaky tests
- Check for hardcoded timeouts
- Use `time.Sleep` sparingly
- Avoid test order dependencies
- Use proper synchronization primitives

## Performance Benchmarks

Key benchmarks to monitor:

```bash
# Label parsing performance
go test -bench=BenchmarkParseCSV ./internal/csv

# GitHub API calls
go test -bench=BenchmarkListLabels ./internal/github

# Sync algorithm performance
go test -bench=BenchmarkSyncLabels ./internal/sync
```

## Resources

- [Go Testing Documentation](https://golang.org/pkg/testing/)
- [Go Testify Framework](https://github.com/stretchr/testify)
- [Go Testing Best Practices](https://golang.org/doc/effective_go#testing)
- [Table-Driven Tests](https://golang.org/wiki/TableDrivenTests)
