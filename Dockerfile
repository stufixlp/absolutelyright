# Build stage
FROM rust:1.80 as builder

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the binary from builder
COPY --from=builder /app/target/release/absolutelyright /app/absolutelyright

# Copy frontend files
COPY frontend ./frontend

# Create directory for database
RUN mkdir -p /app/data

EXPOSE 3003

CMD ["./absolutelyright"]