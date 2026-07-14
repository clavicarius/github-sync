.PHONY: help test test-verbose test-coverage test-race test-short lint fmt clean coverage-report build

help:
	@echo "Available targets:"
	@echo "  make test              - Run all tests"
	@echo "  make test-verbose      - Run tests with verbose output"
	@echo "  make test-coverage     - Run tests with coverage report"
	@echo "  make test-race         - Run tests with race detector"
	@echo "  make test-short        - Run only short tests"
	@echo "  make coverage-report   - Generate HTML coverage report"
	@echo "  make lint              - Run golangci-lint"
	@echo "  make fmt               - Format code with gofmt"
	@echo "  make build             - Build the binary"
	@echo "  make clean             - Clean build artifacts"

# Run all tests
test:
	go test -v ./...

# Run tests with verbose output
test-verbose:
	go test -v -count=1 ./...

# Run tests with coverage
test-coverage:
	go test -v -coverprofile=coverage.out ./...
	go tool cover -func=coverage.out

# Run tests with race detector
test-race:
	go test -race -v ./...

# Run only short tests (skip integration tests)
test-short:
	go test -short -v ./...

# Generate HTML coverage report
coverage-report: test-coverage
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# Run linter
lint:
	golangci-lint run ./...

# Format code
fmt:
	gofmt -w -s .
	goimports -w .

# Build the binary
build:
	go build -o gh-sync-labels ./cmd/gh-sync-labels

# Clean build artifacts
clean:
	rm -f gh-sync-labels coverage.out coverage.html
	go clean -testcache

# Install dependencies
deps:
	go mod download
	go mod tidy

# Run specific test
test-run:
	@read -p "Enter test name (e.g., TestCreateLabel): " test; \
	go test -v -run $$test ./...

# Benchmark tests
bench:
	go test -bench=. -benchmem ./...

# All checks before commit
check: fmt lint test
	@echo "All checks passed!"
